#!/usr/bin/env python
from controllers.irccontroller import IRCController
from controllers.eventcontroller import EventController
from controllers.plugincontroller import PluginController
from controllers.configcontroller import ConfigController
from controllers.datastorecontroller import DatastoreController

from lib.logger import Logger

from models import Channel
from models import Server

import time

class NeuerBot:
	def __init__(self):
		self.eventcontroller  = EventController()
		self.plugincontroller = PluginController(self.eventcontroller)

		self.config = ConfigController()

		self.eventcontroller.set_config(self.config)

		self.irccontrollers = []

	def start(self):
		# Initialize data store
		DatastoreController().set_driver(self.config.get('datastore'))

		for plugin in self.config.get('plugins'):
			Logger.info("Loading plugin '%s'" % plugin)
			self.plugincontroller.load_plugin(plugin)

		for net in self.config.get('ircnets'):
			irc = IRCController(self.eventcontroller)

			# Add channels
			for (channel_name, channel_key) in net['channels']:
				channel = Channel(channel_name, channel_key)
				irc.channels.append(channel)

			# Add servers
			if len(net['servers']) == 0: 
				raise Exception("There must be at least one server defined")

			for (hostname, port, use_ssl, use_ipv6) in net['servers']:
				server = Server(hostname, port, use_ssl, use_ipv6)
				irc.servers.append(server)

			irc.ircnet   = net['ircnet']
			irc.nick     = net['nick']
			irc.altnicks = net['altnicks']
			irc.name     = net['name']
			irc.ident    = net['ident']

			Logger.info("Connecting to %s..." % irc.ircnet)
			irc.connect()

			self.irccontrollers.append(irc)

	def stop(self):
		for irc in self.irccontrollers:
			irc.disconnect()

if __name__ == "__main__":
	bot = None
	try:
		Logger.enable_debug()
		Logger.info("Initializing...")

		bot = NeuerBot()
		bot.start()

		while True:
			# Perform stuff
			time.sleep(1)

	except KeyboardInterrupt:
		Logger.info("Keyboard interrupt detected. Shutting down.")
		bot.stop()

	except Exception, e:
		Logger.fatal("Fatal error: %s" % e)

		if bot:
			bot.stop()
