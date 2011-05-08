from networkclientbase import BufferedNetworkClientBase
from models.ircmessage import IRCMessage

class IRCNetworkClient(BufferedNetworkClientBase):
    def __init__(self):
        BufferedNetworkClientBase.__init__(self)

        self._cb_handle_data       = None
        self._cb_handle_connect    = None
        self._cb_handle_disconnect = None

    def set_handle_data_callback(self, cb):
        self._cb_handle_data = cb

    def set_handle_connect_callback(self, cb):
        self._cb_handle_connect = cb

    def set_handle_disconnect_callback(self, cb):
        self._cb_handle_disconnect = cb

    def handle_data(self, data):
        data = unicode(data, 'utf-8', 'ignore')

        if self._cb_handle_data:
            message = IRCMessage(data)
            self._cb_handle_data(message)

    def handle_connected(self):
        if self._cb_handle_connect:
            self._cb_handle_connect()

    def handle_disconnected(self):
        if self._cb_handle_disconnect:
            self._cb_handle_disconnect()
