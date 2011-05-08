import unittest

from models.server import Server
from models.channel import Channel

from controllers.irccontroller import IRCController
from controllers.eventcontroller import EventController
from lib.net.ircnetworkclient import IRCNetworkClient

class FakeEventController:
    def __init__(self):
        pass

    def register_event(self, *args):
        pass

    def register_timer(self, *args):
        pass

    def release_related(self, *args):
        pass

class IRCNetworkClientMock(IRCNetworkClient):
    def __init__(self):
        IRCNetworkClient.__init__(self)

        self._data_queue = []

    def connect(self, *args, **kwargs):
        self.handle_connected()

    def disconnect(self):
        self.handle_disconnected()

    def clear(self):
        self._data_queue = []

    def get_data(self):
        return self._data_queue

    def send(self, data):
        self._data_queue.append(data)

class TestIRCController(unittest.TestCase):
    def setUp(self):
        self._event_controller = FakeEventController()

        self._irc = IRCController(self._event_controller, clientclass = IRCNetworkClientMock)

        # Setup IRCController
        fakeserver = Server("foo", 6667)
        self._irc.add_server(fakeserver)

        self._irc._ircnet   = "FakeIRCNet"
        self._irc._nick     = "Nick"
        self._irc._name     = "Name"
        self._irc._ident    = "Ident"

        # "connect"
        self._irc.connect()

        # Make sure the buffer is clear
        self._irc.flush_output()
        self._irc._connection.clear()

    def tearDown(self):
        self._irc.disconnect()

    def testMessageOrdering(self):
        # Send some messages and wait for them to be sent to
        # our stubbed socket
        self._irc.privmsg("Foo", "C")
        self._irc.privmsg("Foo", "A")
        self._irc.privmsg("Foo", "B")
        self._irc.flush_output()

        expected = [
            'PRIVMSG Foo :C\r\n',
            'PRIVMSG Foo :A\r\n',
            'PRIVMSG Foo :B\r\n',
        ]

        self.assertEqual(self._irc._connection.get_data(), expected)

    def testMessagePriorities(self):
        self._irc.privmsg("Foo", "B")
        self._irc.quit("Quit now")
        self._irc.privmsg("Foo", "A")
        self._irc.flush_output()

        expected = [
            'QUIT :Quit now\r\n',
            'PRIVMSG Foo :B\r\n',
            'PRIVMSG Foo :A\r\n',
        ]

        self.assertEqual(self._irc._connection.get_data(), expected)
