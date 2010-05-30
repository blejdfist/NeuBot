from lib import Plugin

class PluginRaisesInInit(Plugin):
	def __init__(self):
		self.author = "Jim Persson"
		self.version = "0.0"

		self.event.register_command("foo", self.cmd_foo)

		raise Exception("Something went wrong during initialization")

	def cmd_foo(self, irc, params):
		"""Does nothing"""
