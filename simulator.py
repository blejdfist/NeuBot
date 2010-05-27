#!/usr/bin/env python
from simulator import Simulator
from lib import Logger
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-p", "--plugins", dest="plugins", help="List of plugins to load separated by commas")
parser.add_option("-d", "--debug",   default=False, action="store_true", dest="debug", help="Enable debug log")

(options, args) = parser.parse_args()

if options.debug:
	Logger.enable_debug()

sim = Simulator()
sim.start()

sim.load_plugin("corecommands", "core")
sim.load_plugin("aclcommands", "core")

if options.plugins:
	plugins = options.plugins.split(",")

	for plugin in plugins:
		Logger.info("Loading %s", plugin)
		sim.load_plugin(plugin)

while True:
	try:
		input = raw_input("Simulator# > ")
	except EOFError:
		print "quit"
		break

	if input == "quit":
		break

	sim.msg_channel(input)

sim.stop()
