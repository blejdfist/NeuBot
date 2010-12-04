#!/usr/bin/env python
from simulator.simulator import Simulator
from lib.logger import Logger
from lib.util.commandshell import CommandShell
from controllers.plugincontroller import PluginController

from optparse import OptionParser
import sys

@CommandShell.expander
def get_available_plugins():
    result = {}
    for path, candidate in PluginController().plugin_candidates():
        result[candidate] = None
    return result

@CommandShell.expander
def get_loaded_plugins():
    result = {}

    for name in PluginController().get_loaded_plugins():
        result[name] = None

    return result

parser = OptionParser()
parser.add_option("-p", "--plugins", dest="plugins", help="List of plugins to load separated by commas")
parser.add_option("-d", "--debug",   default=False, action="store_true", dest="debug", help="Enable debug log")

(options, args) = parser.parse_args()

if options.debug:
    Logger.set_loglevel("DEBUGL2")

sim = Simulator()

sim.load_plugin("corecommands", "core")
sim.load_plugin("aclcommands", "core")

if options.plugins:
    plugins = options.plugins.split(",")

    for plugin in plugins:
        Logger.info("Loading %s" % plugin)
        try:
            sim.load_plugin(plugin)
        except Exception as e:
            Logger.log_traceback(sim)
            sys.exit(1)

command_tree = {
    "!load":   get_available_plugins,
    "!unload": get_loaded_plugins,
    "!reload": get_loaded_plugins,
}

shell = CommandShell()
shell.set_parse_tree(command_tree)

# Start simulator and wait for the initialization events to finish
sim.start()
sim.wait_for_events()
sim.flush()

while True:
    try:
        input = shell.input("Simulator# > ")
    except (EOFError, KeyboardInterrupt):
        print "quit"
        break

    if input == "quit":
        break

    sim.msg_channel(input)
    sim.wait_for_events()
    sim.flush()

sim.stop()
