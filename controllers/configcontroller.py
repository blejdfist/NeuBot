from lib.util import Singleton
import sys

##
# @class ConfigController
# Contains the configuration
class ConfigController(Singleton):
	def __init__(self):
		if not hasattr(self, 'botconfig'):
			self.load()

	def load(self):
		if hasattr(self, "botconfig"):
			del self.botconfig

		if sys.modules.has_key('config'):
			del sys.modules['config']

		mod = __import__("config")
		self.botconfig = mod.Bot

	##
	# Get the value for a configuration option
	# @param key Configuration option
	# @return Option value
	def get(self, key):
		if self.botconfig.has_key(key):
			return self.botconfig[key]

		return None
