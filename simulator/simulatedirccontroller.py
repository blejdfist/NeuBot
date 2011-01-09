from controllers.irccontroller import IRCController

class SimulatedIRCController(IRCController):
    def __init__(self, eventcontroller, socketinstance):
        IRCController.__init__(self, eventcontroller)

        self._connection = socketinstance

    def connect(self):
        self._connection.OnConnect    = lambda inst : IRCController._handle_connect(self, inst)
        self._connection.OnDisconnect = lambda inst : IRCController._handle_disconnect(self, inst)
        self._connection.OnData       = lambda data, inst : IRCController._handle_data(self, data, inst)

        self._connection.connect()
