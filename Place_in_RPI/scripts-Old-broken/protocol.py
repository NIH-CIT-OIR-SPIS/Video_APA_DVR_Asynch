"""A module for defining the SCORHE_protocol.

The SCORHE_protocol is used for communication between the Python server
(SCORHE_server2.py) and the Raspberry Pi camera clients
(SCORHE_client2.py) as well as application clients (SCORHE_recorder_gui.m).
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
import inspect
import logging
import queue
import re
import sys
import threading
import traceback

try:
    from typing import Optional, Callable, Tuple, Union
except ImportError:
    class _typing:
        def __getitem__(self, item):
            return item
    Optional = _typing()
    Callable = _typing()
    Union = _typing()
    Tuple = _typing()

logger = logging.getLogger(__name__)


class syntax:
    argDelimiter = bytes([28])  # b','
    statementDelimiter = bytes([29])  # b')'
    typeValueDelimiter = bytes([30])  # b':'
    keyArgsDelimiter = bytes([31])  # b'('

    @staticmethod
    def formatMessage(message: Union[bytearray, bytes]) -> str:
        return message \
            .replace(syntax.argDelimiter, b', ') \
            .replace(syntax.statementDelimiter, b');') \
            .replace(syntax.typeValueDelimiter, b':') \
            .replace(syntax.keyArgsDelimiter, b'(').decode()


class Protocol:
    """A Protocol contains a MessageBuilder and a MessageHandler."""

    def __init__(self, handler: 'MessageHandler', builder: 'MessageBuilder'):
        self.builder = builder
        self.handler = handler

    def buildMessage(self, *args) -> bytes:
        return self.builder.buildMessage(*args)

    def handleBuffer(self, *args) -> bytes:
        return self.handler.handleBuffer(*args)


class ProtocolRules:
    """Parent class for MessageBuilder and MessageHandler.

    Both child classes use rules to map message IDs to functions that handle
    them.
    """

    def __init__(self):
        self.rules = {}

    class Rule:
        def __init__(self,
                     argsFormat: str,
                     handler: Optional[Callable[..., Optional[Tuple[Union[str, int, float, bool], ...]]]],
                     debugstr: str):
            self.argsFormat = argsFormat
            self.handler = handler
            self.debugstr = debugstr

    def addRule(self,
                key: str,
                argsFormat: str='',
                handler: Optional[Callable[..., Optional[Tuple[Union[str, int, float, bool], ...]]]]=None,
                debugstr: str='',
                ) -> None:
        self.rules[key] = ProtocolRules.Rule(argsFormat, handler,
                                             debugstr)


class MessageBuilder(ProtocolRules):
    """Maps message IDs to functions that construct corresponding messages."""

    def buildMessage(self,
                     key: str,
                     *args: Union[str, int, bool, float]) -> bytes:
        if key not in self.rules:
            raise Exception('Key {} not found in ruleset {}'.format(
                    key, self.rules.keys()))
        rule = self.rules[key]
        message = key.encode() + syntax.keyArgsDelimiter
        if rule.handler:
            outputArgs = rule.handler(*args)
            if len(rule.argsFormat) != len(outputArgs):
                raise Exception(('Cannot build message for "{}": ' +
                                 'expected {} arguments, got {}').format(
                        key, len(rule.argsFormat),
                        len(outputArgs)))
            for i in range(len(rule.argsFormat)):
                argFormat = rule.argsFormat[i]
                message += argFormat.encode() + syntax.typeValueDelimiter
                message += MessageBuilder._pack(argFormat, outputArgs[i])
                if i < len(rule.argsFormat) - 1:
                    message += syntax.argDelimiter
        message += syntax.statementDelimiter
        return message

    @staticmethod
    def _pack(argFormat: str, arg: Union[str, int, bool, float]) -> bytes:
        return str(arg).encode()


class MessageHandler:
    """Maps message IDs to functions that handle those messages."""

    def __init__(self, taskQueue: 'EventProtocol', messageHandler, errorHandler):
        self.taskQueue = taskQueue
        self.messageHandler = messageHandler
        self.errorHandler = errorHandler
        self._words_regex = re.compile(' ([a-zA-Z])')
        self._words_replace = lambda match: match.group(1).upper()

    def assertHandler(self, key: str, signature: str='', func: Optional[Callable]=None) -> None:
        f = self.getHandler(key)
        funcArgTypes = self.getSignature(f).decode()
        if funcArgTypes != signature:
            raise RuntimeError('Expected a function with signature {}, '
                               'got {}'.format(signature, funcArgTypes))
        if func != f:
            raise RuntimeError('Function with given key is not the expected '
                               'function.')

    def getHandler(self, key: str) -> Callable:
        """Gets the function that a given key could address from the message handler.

        This function tries to get an attribute with the given key, converted to
        camelCase ('this is a test' -> 'thisIsATest') or the key starting after
        the first space (nominally to use properties by skipping the 'set' at
        the beginning of the key).

        :param key: The key used by the protocol to address the wanted function.
        :return: The found function. If the function wasn't found, a
            RuntimeError is thrown.
        """
        try:
            f = getattr(self.messageHandler,
                        self._words_regex.sub(self._words_replace, key))
        except AttributeError:
            try:
                f = getattr(self.messageHandler,
                            self._words_regex.sub(self._words_replace, key[key.index(' ') + 1:]))
            except AttributeError:
                raise RuntimeError('missing handler or property ' + key)
        return f

    @staticmethod
    def getSignature(func: Callable) -> bytes:
        """Gets the signature of a function.

        Only strings (S), ints (i), floats (d) or bools (?) are encoded.
        Other types are encoded as spaces.

        :param func: The function to analyze.
        :return: A bytes object which represents the parameters of the function.
        """
        sig = inspect.signature(func).parameters
        funcArgTypes = b''
        for arg in sig.values():
            ann = arg.annotation
            if ann == str:
                funcArgTypes += b'S'
            elif ann == int:
                funcArgTypes += b'i'
            elif ann == float:
                funcArgTypes += b'd'
            elif ann == bool:
                funcArgTypes += b'?'
            else:
                funcArgTypes += b' '
        return funcArgTypes

    def handleBuffer(self, buffer: bytes) -> bytes:
        statements = buffer.split(syntax.statementDelimiter)
        for statement in statements[:-1]:
            try:
                key, arguments = statement.split(syntax.keyArgsDelimiter)
                key = key.decode()
            except Exception as err:
                self._error(statement, str(err))
            else:
                try:
                    f = self.getHandler(key)
                except RuntimeError:
                    self._error(
                            statement,
                            'No such handler {}'.format(key)
                    )
                    continue
                funcArgTypes = self.getSignature(f)
                outputArgs = ()
                if arguments:
                    arguments = arguments.split(syntax.argDelimiter)
                if len(arguments) != len(funcArgTypes):
                    self._error(
                            statement,
                            'Expected {} arguments, got {}'.format(
                                    len(funcArgTypes),
                                    len(arguments)))
                    continue
                for expArgType, arg in zip(funcArgTypes, arguments):
                    argType, value = arg.split(syntax.typeValueDelimiter)
                    if len(argType) != 1:
                        self._error(
                                statement,
                                'Expected argtype of length 1, got "{}"'.format(
                                        argType))
                        break
                    if expArgType != argType[0]:
                        self._error(
                                statement,
                                'Expected argtype {}, got {}'.format(
                                        expArgType,
                                        argType))
                        break
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
                self.taskQueue.qcall(f, *outputArgs)

        self.taskQueue.flush()
        return statements[-1]

    def _error(self, statement: bytes, message: str) -> None:
        self.errorHandler.error(self.messageHandler, 'Cannot parse message {}: {}'.format(
                syntax.formatMessage(statement), message))


class EventProtocol:
    """Thread-safe method to let outside threads call functions."""

    def __init__(self):
        self.queue = queue.Queue()
        self.wakeEvent = threading.Event()
        self.closeEvent = threading.Event()
        self.semaphore = threading.Semaphore()

    def call(self, handler: Callable, *args) -> None:
        """Enqueue an event and wake up the thread handling the events."""
        self.queue.put((handler, args))
        self.flush()

    def qcall(self, handler: Callable, *args) -> None:
        """Enqueue an event without flushing."""
        with self.semaphore:
            self.queue.put((handler, args))

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
                        f(*args)
                    except Exception as err:
                        logger.exception(err)
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
