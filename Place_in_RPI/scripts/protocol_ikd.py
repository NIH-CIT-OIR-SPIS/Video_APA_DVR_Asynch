"""A module for defining the SCORHE_protocol.

The SCORHE_protocol is used for communication between the Python server
(SCORHE_server.py) and the Raspberry Pi camera clients
(SCORHE_client.py).
Messages are sent through network sockets and can pass several types of
data, including integers, double floating point numbers, and strings.

A SCORHE_protocol message contains a message ID and a list of arguments.
Each argument has a type, which can be one of the following:

    ?: boolean (true or false)
    i: integer
    d: double precision floating point number (aka "double")
    S: string (text)

Special, unused ASCII codes are used to delimit parts of the message, to
allow the protocol language to be regular.
(http://en.wikipedia.org/wiki/Regular_language)

Though when you "decode" a message for debugging, it shows symbols like
:,();, these characters ARE allowed in string messages.
"""

import logging
import queue
import sys
import threading
import traceback
from typing import Callable, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class Syntax:
    """A utility class for constants for the messages sent via this protocol.

    This class dictates the delimiter for arguments in a message
    (``argDelimiter``), the delimiter between statements/messages
    (``statementDelimiter``), the delimiter between a type an the parameter
    (``typeValueDelimiter``), and the delimiter between the rest of the message
    and the arguments (``keyArgsDelimiter``).

    An analogy to a regular function definition would be as follows:
    int the statement ``startRecording(bool:True, int:124);``, ``(`` is the
    ``keyArgsDelimiter``, between the statement/function name and the arguments.
    ``:`` is the ``typeValueDelimiter``, between the type of an item and its
    value. ``,`` is the ``argDelimiter``, between each of the arguments.
    Finally, ``);`` is the ``statementDelimiter``, defining the end of a
    statement.

    In reality, the actual delimiters are non-printable characters (and the
    types are single characters, but are not defined in this class). This
    allows the above characters (``(:,);``) to be used inside a message.
    Since non-printable characters make debugging and printing messages hard,
    this class also defines a utility method to replace the delimiters with more
    useful ones (namely, the ones mentioned above).
    """

    argDelimiter = bytes([28])  # file sep, decoded as b', '
    statementDelimiter = bytes([29])  # group sep, decoded as b');'
    typeValueDelimiter = bytes([30])  # record sep, decoded as b':'
    keyArgsDelimiter = bytes([31])  # unit sep, decoded as b'('

    @staticmethod
    def formatMessage(message: bytes) -> str:
        """Formats a message for pretty printing.

        :param message: A message to or from a client that needs to be formatted
            for pretty printing.
        :return: A string with all delimiters replaced with more readable
            delimiters.
        """
        return message \
            .replace(Syntax.argDelimiter, b', ') \
            .replace(Syntax.statementDelimiter, b');') \
            .replace(Syntax.typeValueDelimiter, b':') \
            .replace(Syntax.keyArgsDelimiter, b'(').decode()


class Protocol:
    """A Protocol contains a MessageBuilder and a MessageHandler."""

    def __init__(self, handler: 'MessageHandler', builder: 'MessageBuilder'):
        self.builder = builder
        self.handler = handler

    def buildMessage(self, *args) -> bytes:
        """Builds a message using the given arguments.

        See ``MessageBuilder.buildMessage`` for details.
        """
        return self.builder.buildMessage(*args)

    def handleBuffer(self, *args) -> bytes:
        """Handles the buffer parsed by the listener.

        See ``MessageHandler.handleBuffer`` for details.
        """
        return self.handler.handleBuffer(*args)


class ProtocolRules:
    """Parent class for MessageBuilder and MessageHandler.

    Both child classes use rules to map message IDs to functions that handle
    them.
    """

    def __init__(self):
        self.rules = {}

    class Rule:
        """A class that associates functions with their return types.

        This makes formatting of the messages to the client easier.
        """
        def __init__(self,
                     argsFormat: str,
                     handler: Optional[Callable[..., Optional[Tuple[Union[str, int, float, bool], ...]]]],
                     debugStr: str):
            self.argsFormat = argsFormat
            self.function = handler
            self.debugStr = debugStr

    def addRule(self,
                key: str,
                argsFormat: str='',
                handler: Optional[Callable[..., Optional[Tuple[Union[str, int, float, bool], ...]]]]=None,
                debugStr: str='',
                ) -> None:
        """Sets the handler for a given key.

        The variable ``argsFormat`` dictates what parameters ``handler``
        accepts.

        :param key: The key associated with the rule (like ``set fps``).
        :param argsFormat: A string of the types of the arguments, in order.
        :param handler: The function to be called when this rule is accessed.
        :param debugStr: I have no clue.
        :return: Nothing
        """
        self.rules[key] = ProtocolRules.Rule(argsFormat, handler,
                                             debugStr)


class MessageBuilder(ProtocolRules):
    """Maps message IDs to functions that construct corresponding messages."""

    def buildMessage(self,
                     key: str,
                     *args: Union[str, int, bool, float]) -> bytes:
        """Constructs a byte string to transmit the given message via this protocol.

        :param key: The string key identifying the message (like ``set fps``).
        :param args: Any arguments necessary to define the message.
        :return: A byte string containing the statement for the given message.
        """
        if key not in self.rules:
            raise Exception('Key {} not found in rule set {}'.format(
                    key, self.rules.keys()))
        rule = self.rules[key]
        message = key.encode() + Syntax.keyArgsDelimiter
        if rule.function:
            #print(*args)
            outputArgs = rule.function(*args)
            if len(rule.argsFormat) != len(outputArgs):
                raise Exception(('Cannot build message for "{}": '
                                 'expected {} arguments, got {}').format(
                        key, len(rule.argsFormat),
                        len(outputArgs)))
            for i in range(len(rule.argsFormat)):
                argFormat = rule.argsFormat[i]
                message += argFormat.encode() + Syntax.typeValueDelimiter
                message += MessageBuilder._pack(argFormat, outputArgs[i])
                if i < len(rule.argsFormat) - 1:
                    message += Syntax.argDelimiter
        message += Syntax.statementDelimiter
        return message

    @staticmethod
    def _pack(_argFormat: str, arg: Union[str, int, bool, float]) -> bytes:
        return str(arg).encode()


class MessageHandler(ProtocolRules):
    """Maps message IDs to functions that handle those messages."""

    def __init__(self, taskQueue: 'AsyncFunctionQueue', showErrors: bool=True):
        """Creates an object that polls for messages and processes them.

        :param taskQueue: An object used to poll the connection for messages
            from the client.
        :param showErrors: Whether errors should be printed when they occur.
        """
        ProtocolRules.__init__(self)
        self.taskQueue = taskQueue  # type: AsyncFunctionQueue
        self.showErrors = showErrors  # type: bool

    def handleBuffer(self, buffer: bytes, *inputArgs) -> bytes:
        """Parses a buffer retrieved from the client(s).

        This function parses all completed statements in the given buffer,
        constructing a tuple of all the parsed arguments, and forwards the
        arguments along with the ``inputArgs`` to the ``taskQueue`` to handle.
        The function then returns the incomplete statement fragment at the end
        of the given buffer.

        :param buffer: The buffer parsed from the connection to the clients.
        :param inputArgs: Any parameters that should be passed to handling
            function (generally just the server and client)
        :return: The part of the buffer that was not parsed as a statement. May
            be empty.
        """
        statements = buffer.split(Syntax.statementDelimiter)
        # ignore the last in the split since it's either empty or an incomplete
        # statement fragment.
        for statement in statements[:-1]:
            outputArgs = ()
            try:
                key, arguments = statement.split(Syntax.keyArgsDelimiter)
                key = key.decode()
            except Exception as err:
                self._error(statement, str(err))
            else:
                if key in self.rules:
                    rule = self.rules[key]
                    if arguments:
                        arguments = arguments.split(Syntax.argDelimiter)
                    if len(arguments) != len(rule.argsFormat):
                        if self.showErrors:
                            self._error(
                                    statement,
                                    'Expected {} arguments, got {}'.format(
                                            len(rule.argsFormat),
                                            len(arguments)))
                        break
                    # Break up the arguments
                    for arg in arguments:
                        argType, value = arg.split(Syntax.typeValueDelimiter)
                        if argType == b'i':
                            outputArgs += int(value),
                        elif argType == b'd':
                            outputArgs += float(value),
                        elif argType == b'?':
                            if value == b'True':
                                outputArgs += True,
                            else:
                                outputArgs += False,
                        elif argType == b'S':
                            outputArgs += value.decode(),
                        else:
                            self._error(statement,
                                        'Unrecognized argument type: {}'.format(argType))
                            break
                    try:
                        # Call the parsed function
                        if rule.function:
                            self.taskQueue.qcall(rule.function,
                                                 *(inputArgs + outputArgs))
                    except Exception as err:
                        self._error(
                                statement,
                                'Error executing handler for {} ({}): {}'.format(
                                        key, outputArgs, err))
                        traceback.print_tb(sys.exc_info()[2])
                else:
                    self._error(statement,
                                'Key {} not found in rule set: {}'.format(
                                        key, self.rules.keys()))
        self.taskQueue.flush()
        return statements[-1]

    @staticmethod
    def _error(statement: bytes, message: str) -> None:  # *****************************************NC: ERROR HERE **************************************
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Cannot parse message {}: {}'.format(
                    Syntax.formatMessage(statement), message))


class AsyncFunctionQueue:
    """A queue that calls functions on a separate thread.

    Functions can also be batched with ``qcall`` + ``flush``.
    """

    def __init__(self):
        self.queue = queue.Queue()
        self.wakeEvent = threading.Event()
        self.closeEvent = threading.Event()
        self.semaphore = threading.Semaphore()

    def call(self, callback: Callable, *args) -> None:
        """Enqueue an event and wake up the thread handling the events."""
        self.queue.put((callback, args))
        self.flush()

    def qcall(self, callback: Callable, *args) -> None:
        """Enqueue an event without flushing."""
        with self.semaphore:
            self.queue.put((callback, args))

    def flush(self) -> None:
        """Wake up the thread handling the events."""
        self.wakeEvent.set()

    def start(self) -> None:
        """Blocks until finish() is called from another thread."""
        while True:
            self.wakeEvent.wait()
            with self.semaphore:
                while not self.queue.empty():
                    f, args = self.queue.get()
                    try:
                        #print(*args)
                        f(*args)
                    except Exception as err:
                        logger.error('ERROR: {}'.format(err))
                        traceback.print_tb(sys.exc_info()[2])
                    self.queue.task_done()
                if self.closeEvent.is_set():
                    self.wakeEvent.clear()
                    return
                self.wakeEvent.clear()

    def finish(self) -> None:
        """Call from another thread to finish handling the queue."""
        self.closeEvent.set()
        self.flush()
