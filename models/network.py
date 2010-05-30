from models.channel import Channel

class Network:
	def __init__(self, name):
		self.name = name
		self.channels = []

	def __repr__(self):
		return "<Network name="+ self.name + ">"

	def __str__(self):
		return self.name

	def num_channels(self):
		return len(self.channels)

	def add_channel(self, channel):
		if not isinstance(channel, Channel):
			raise Exception("add_channel: Must send Channel instance")

		self.channels.append(channel)

	def del_channel(self, channel):
		if type(channel) == str:
			for chan in self.channels:
				if chan.name == channel:
					self.channels.remove(chan)
					return True

		try:
			self.channels.remove(channel)
		except ValueError:
			return False

		return True

