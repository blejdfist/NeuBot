from lib import Plugin
from lib.util import TableFormatter

from controllers.aclcontroller import ACLController

class CoreCommands(Plugin):
	def __init__(self):
		self.author = "Jim Persson"
		self.version = "1.0"

		self.event.register_command("help", self.cmd_help)

	def list_commands(self, irc):
		acl = ACLController()
		commands = self.event.get_all_commands()
		num_columns = 6

		cmdlist = []

		for command in commands:
			callbacks = self.event.get_command_callbacks(command)
			for _, _, privileged in callbacks:
				if privileged and not acl.check_access(irc.message.source, command):
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

		for row in table.get_table():
			irc.reply(row)

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
					irc.reply(plugin.name + " - " + command)

				# Filter out empty lines
				lines = filter(lambda x : len(x) > 0, doc.splitlines())

				# Find minimum whitespace so we can normalize doc-comment
				min_whitespace = min(map(lambda x : len(x) - len(x.lstrip()), lines))

				for line in lines:
					line = line[min_whitespace:]
					irc.reply(line)

		if not found_help:
			irc.reply("No help available")

	def cmd_help(self, irc, params):
		if len(params) == 0:
			self.list_commands(irc)
		else:
			self.help_for_command(irc, params[0])
