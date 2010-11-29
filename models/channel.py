from models.ircuser import IRCUser

class Channel:
    def __init__(self, name, password = None):
        self.password = password
        self.name = name
        self.is_joined = False
        self.who = []
        self.topic = None

    def __repr__(self):
        extra = []

        extra.append("name=" + self.name)

        if self.password:
            extra.append("password=" + self.password)

        return "<Channel %s>" % (" ".join(extra),)

    def __str__(self):
        return self.name

    def add_user(self, user):
        if not isinstance(user, IRCUser):
            raise Exception("add_user: Must send IRCUser instance")

        if self.who.count(user) == 0:
            self.who.append(user)

    def del_user(self, user):
        if not isinstance(user, IRCUser):
            raise Exception("del_user: Must send IRCUser instance")

        if self.who.count(user) != 0:
            self.who.remove(user)

    def num_users(self):
        return len(self.who)
