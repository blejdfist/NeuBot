from lib import Plugin

class NormalPlugin(Plugin):
	def __init__(self):
		self.author = "Jim Persson"
		self.version = "0.0"

		self.event.register_command("foo", self.cmd_foo)

	def cmd_foo(self, irc, params):
		"""Does nothing"""
