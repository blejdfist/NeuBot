from controllers.eventcontroller import EventController
from controllers.irccontroller import IRCController
from controllers.datastorecontroller import DatastoreController
from controllers.plugincontroller import PluginController
from controllers.ircnetscontroller import IRCNetsController
from controllers.configcontroller import ConfigController

from simulatedircnetworkclient import SimulatedIRCNetworkClient

class Simulator:
    def __init__(self):
        self.event = EventController()
        self.plugin = PluginController()

        # Make sure the simulated user have access to all commands
        ConfigController().get('masters').append('*!*@*')
        ConfigController().set('irc.rate_limit_wait_time', 0)

        # Configuration
        # This must match the values in SimulatedIRCNetworkClient
        simulated_ircnet = {
            "ircnet":    "SimuNet",
            "nick":      "NeuBot",
            "altnicks":  [],
            "name":      "Simulated Bot",
            "ident":     "neubot",
            "servers": [
                ("irc.example.org", 6667, False, False),
            ],
            "channels": [
                ("#simulator", None),
            ]
        }

        # Initiate the IRCController and tell it to use our fake clientclass
        # so that it won't actually connect to a real server
        irc = IRCController(self.event, clientclass = SimulatedIRCNetworkClient)
        irc.set_configuration(simulated_ircnet)

        # Register server with ircnetscontroller
        IRCNetsController().add_ircnet(irc.get_ircnet_name(), irc)

        self._irc = irc

        # Initialize datastore
        DatastoreController().set_driver("data/simulator.db")

    def load_plugin(self, name, search_dir = None):
        self.plugin.load_plugin(name, search_dir)

    def feed_data(self, data):
        self._socket.server_raw(data)

    def msg_channel(self, message):
        self._socket.server_user_response("PRIVMSG", "#simulator :" + message)

    def start(self):
        self._irc.connect()
        self._socket = self._irc.get_connection()

    def stop(self):
        self._irc.disconnect()
        self.plugin.unload_all()

    ##
    # Wait for all dispatched event threads to complete
    def wait_for_events(self):
        self.event.wait_for_pending_events()

    ##
    # Wait for all queued output to be sent to the server
    # (the simulated socket in this case)
    def flush(self):
        self._irc.flush_output()
