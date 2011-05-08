from lib.logger import Logger
from lib.net.ircnetworkclient import IRCNetworkClient

import ircdef
import re

class SimulatedIRCNetworkClient(IRCNetworkClient):
    def __init__(self):
        IRCNetworkClient.__init__(self)

        # Bot nick and server name
        # these settings much match what's being used
        # in simulator.py
        self.bot_nick = "NeuBot"
        self.bot_ident = "neubot"
        self.bot_host = "example.org"
        self.server_name = "irc.example.org"

        self.sim_nick = "MrSim"
        self.sim_ident = "mrsim"
        self.sim_host = "example.org"

    ##
    # Simulate raw data from the server
    #
    # @param data Raw data that seems to come from the server
    def server_raw(self, data):
        self.handle_data(data)

    ##
    # Simulate a server response and feed it into the bot
    #
    # @param code Numeric code or command
    # @param params Parameters to the code
    def server_response(self, code, params):
        data = ":%s %s %s" % (self.server_name, str(code), params)
        self.server_raw(data)

    ##
    # Simulate data being sent by simulator user
    # Example: server_use_response("PRIVMSG", "#channel :Hello")
    #
    # @param code Command from the user
    # @param params Parameters to the command
    def server_user_response(self, code, params):
        data = ":%s!%s@%s %s %s" % (self.sim_nick, self.sim_ident, self.sim_host, code, params)
        self.server_raw(data)

    def connect(self, *args, **kwargs):
        self.handle_connected()
        self.server_response(ircdef.RPL_MYINFO, "FakeIRC iowghraAsORTVSxNCWqBzvdHtGp lvhopsmntikrRcaqOALQ")

    def disconnect(self):
        self.handle_disconnected()

    def send(self, data):
        params = data.split()
        if len(params) == 0:
            return

        cmd = params[0]

        if cmd == "JOIN":
            self.server_user_response("JOIN", ":" + params[1])
            self.server_user_response(ircdef.RPL_ENDOFNAMES, "%s :/End of /NAMES list." % params[1])
        elif cmd == "WHO":
            self.server_response(ircdef.RPL_WHOREPLY, "%s %s %s %s %s %s H :0 %s" % (
                self.bot_nick,
                params[1],
                self.bot_ident,
                self.bot_host,
                self.server_name,
                self.bot_nick,
                "The NeuBot"))

            self.server_response(ircdef.RPL_ENDOFWHO, "%s %s :End of /WHO list." % (self.bot_nick, params[1],))

        elif cmd == "PRIVMSG":
            match = re.match("PRIVMSG (.*?) :(.*)", data)
            channel, message = match.groups()

            print "\033[1;37m[%s:PRIVMSG %s]\033[0m %s" % (self.bot_nick, channel, message)

        elif cmd == "NOTICE":
            match = re.match("NOTICE (.*?) :(.*)", data)
            channel, message = match.groups()

            print "\033[1;35m<%s:NOTICE %s>\033[0m %s" % (self.bot_nick, channel, message)

        elif cmd == "PING":
            match = re.match("PING (.*)", data)
            self.server_response("PONG", match.group(1))

        else:
            Logger.debug("Unhandled: " + data.strip())
