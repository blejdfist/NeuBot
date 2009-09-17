import re

class IRCUser:
	whoparser = re.compile("^(.*?)!(.*?)@(.*?)$")

	def __init__(self, who):
		self.nick = None
		self.ident = None
		self.hostname = None

		match = IRCUser.whoparser.match(who)
		if match:
			self.nick, self.ident, self.hostname = match.groups()

	def __eq__(self, other):
		return (self.nick == other.nick and 
				self.ident == other.ident and
				self.hostname == other.hostname)

	def is_matching(self, who):
		match = IRCUser.whoparser.match(who.replace(".", "\\.").replace("*", ".*?"))

		if match is None:
			raise Exception("Illegal hostmask")

		(nickReg, identReg, hostnameReg) = match.groups()

		searches = [
			("^" + nickReg + "$", self.nick),
			("^" + identReg + "$", self.ident),
			("^" + hostnameReg + "$", self.hostname)
		]

		return reduce(lambda x,y : (x and y), [re.match(reg, str) != None for (reg,str) in searches])

