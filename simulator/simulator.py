from controllers.irccontroller import IRCController
from controllers.eventcontroller import EventController
from controllers.datastorecontroller import DatastoreController
from controllers.plugincontroller import PluginController
from controllers.ircnetscontroller import IRCNetsController

from models import Channel, Server

from fakesocket import FakeSocket
from simulatedirccontroller import SimulatedIRCController

# Override socket class
import lib.net.netsocket
lib.net.netsocket.AsyncBufferedNetSocket = FakeSocket

class Simulator:
	def __init__(self):
		self.bot_nick = "NeuBot"
		self.bot_ident = "neubot"
		self.bot_host = "example.org"

		self.server_name = "irc.example.org"

		self.event = EventController()
		self.plugin = PluginController()
		self.socket = FakeSocket(server_name = self.server_name, bot_nick = self.bot_nick, bot_ident = self.bot_ident, bot_host = self.bot_host)

		irc = SimulatedIRCController(self.event, self.socket)

		# Setup bot
		irc.ircnet = "SimuNet"
		irc.nick = self.bot_nick
		irc.name = "The NeuBot"
		irc.ident = self.bot_ident

		# Add fake server
		irc.servers.append(Server(self.server_name, 6667))

		# Register server with ircnetscontroller
		IRCNetsController().add_ircnet("SimuNet", irc)

		# Add fake channels
		irc.channels.append(Channel('#simulator'))

		self.irc = irc

		# Initialize datastore
		DatastoreController().set_driver("data/simulator.db")

	def load_plugin(self, name, search_dir = "plugins"):
		self.plugin.load_plugin(name, search_dir)

	def feed_data(self, data):
		self.socket.server_raw(data)

	def msg_channel(self, message):
		self.socket.server_user_response("PRIVMSG", "#simulator :" + message)

	def start(self):
		self.irc.connect()

	def stop(self):
		self.irc.disconnect()

