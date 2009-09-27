from models import IRCUser

class UserController:
	def __init__(self):
		self.users = []

	def add_user(self, user):
		self.users.append(user)

	def del_user(self, user):
		self.users.remove(user)

	def get_user(self, whostring):
		matching = IRCUser(whostring)

		try:
			index = self.users.index(matching)
			#print "Returning old user %s" % self.users[index]
			return self.users[index]
		except:
			self.add_user(matching)
			#print "Adding new user %s" % matching
			return matching
