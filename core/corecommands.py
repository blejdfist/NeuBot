from lib import Plugin
from lib import Logger
from lib.util import TableFormatter

from controllers.aclcontroller import ACLController

class CoreCommands(Plugin):
	def __init__(self):
		self.author = "Jim Persson"
		self.version = "1.0"

		self.event.register_command("help",    self.cmd_help)
		self.event.register_command("debug",   self.cmd_debug, True)
		self.event.register_command("quit",    self.cmd_quit,  True)

		self.event.register_command("load",    self.cmd_load,   True)
		self.event.register_command("reload",  self.cmd_reload, True)
		self.event.register_command("unload",  self.cmd_unload, True)

	def list_commands(self, irc):
		acl = ACLController()
		commands = self.event.get_all_commands()
		num_columns = 6

		cmdlist = []

		for command in commands:
			callbacks = self.event.get_command_callbacks(command)

			masters = self.config.get('masters')
			if masters:
				masterAccess = reduce(lambda x,y : x or y, [irc.message.source.is_matching(hostmask) for hostmask in masters])
			else:
				masterAccess = False

			for _, _, privileged in callbacks:
				if privileged and not (masterAccess or acl.check_access(irc.message.source, command)):
					pass
				else:
					if privileged:
						cmdlist.append("*" + command)
					else:
						cmdlist.append(" " + command)

		table = TableFormatter(['']*num_columns, 'Available commands')

		while len(cmdlist) > 0:
			row = cmdlist[0:num_columns]
			row += [' '] * (num_columns - len(row))
			table.add_row(row)
			del cmdlist[0:num_columns]

		for row in table.get_table(column_headers = False):
			irc.notice(irc.message.source.nick, row)

	def help_for_command(self, irc, command):
		acl = ACLController()
		callbacks = self.event.get_command_callbacks(command)
		found_help = False

		if callbacks is None:
			irc.reply("No such command")
			return

		for plugin, callback, privileged in callbacks:
			# Don't show help for privileged commands if the user doesn't have access
			if privileged and not acl.check_access(irc.message.source, command):
				continue

			doc = callback.__doc__
			if doc:
				found_help = True

				if hasattr(plugin, "name"):
					irc.notice(irc.message.source.nick, plugin.name + " - " + command)

				# Filter out empty lines
				lines = filter(lambda x : len(x) > 0, doc.splitlines())

				# Find minimum whitespace so we can normalize doc-comment
				min_whitespace = min(map(lambda x : len(x) - len(x.lstrip()), lines))

				for line in lines:
					line = line[min_whitespace:]
					irc.notice(irc.message.source.nick, line)

		if not found_help:
			irc.reply("No help available")

	def cmd_help(self, irc, params):
		if len(params) == 0:
			self.list_commands(irc)
		else:
			self.help_for_command(irc, params[0])

	def cmd_debug(self, irc, params):
		"""
		Enable or disable debugging
			debug [enable|disable]"""

		if len(params) == 0:
			irc.reply("Not enough parameters")
			return

		if params[0] == 'enable':
			Logger.enable_debug(True)
			irc.reply("Debugging enabled")
		elif params[0] == 'disable':
			Logger.enable_debug(False)
			irc.reply("Debugging disabled")
		else:
			irc.reply("Invalid option")

	def cmd_quit(self, irc, params):
		"""Shuts down the bot"""
		self.event.dispatch_system_event("BOT_QUIT")

	def cmd_load(self, irc, params):
		"""Loads the named plugin"""

		if len(params) == 0:
			irc.reply("Must supply the name of a plugin to load")
			return

		try:
			self.plugin.load_plugin(params[0])
			irc.reply("Plugin loaded")
		except Exception, e:
			irc.reply(e)

	def cmd_reload(self, irc, params):
		"""Reloads the named plugin"""

		if len(params) == 0:
			irc.reply("Must supply the name of a plugin to reload")
			return

		try:
			self.plugin.reload_plugin(params[0])
			irc.reply("Plugin (re)loaded")
		except Exception, e:
			irc.reply(e)

	def cmd_unload(self, irc, params):
		"""Unloads the named plugin"""

		if len(params) == 0:
			irc.reply("Must supply the name of a plugin to unload")
			return

		try:
			self.plugin.unload_plugin(params[0])
			irc.reply("Plugin unloaded")
		except Exception, e:
			irc.reply(e)


