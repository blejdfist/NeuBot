from controllers import IRCController

class SimulatedIRCController(IRCController):
	def __init__(self, eventcontroller, socketinstance):
		IRCController.__init__(self, eventcontroller)

		self.connection = socketinstance

	def connect(self):
		self.connection.OnConnect    = lambda inst : IRCController._handle_connect(self, inst)
		self.connection.OnDisconnect = lambda inst : IRCController._handle_disconnect(self, inst)
		self.connection.OnData       = lambda data, inst : IRCController._handle_data(self, data, inst)

		self.connection.connect()

