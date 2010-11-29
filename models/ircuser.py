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

    def __str__(self):
        return "<IRCUser %s!%s@%s>" % (self.nick, self.ident, self.hostname)

    def __repr__(self):
        return "<IRCUser %s!%s@%s>" % (self.nick, self.ident, self.hostname)

    def __eq__(self, other):
        return (self.nick == other.nick and 
                self.ident == other.ident and
                self.hostname == other.hostname)

    def change(self, nick = None, ident = None, hostname = None):
        if nick:
            self.nick = nick

        if ident:
            self.ident = ident

        if hostname:
            self.hostname = hostname

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

        return reduce(lambda x, y : (x and y), [re.match(reg, string) != None for (reg, string) in searches])

