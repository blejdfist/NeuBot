class Server:
    def __init__(self, hostname, port, use_ssl = False, use_ipv6 = False):
        self.hostname = hostname
        self.port     = port
        self.use_ssl  = use_ssl
        self.use_ipv6 = use_ipv6

    def __repr__(self):
        return "<Server %s:%d>" % (self.hostname, self.port)

    def __str__(self):
        return "%s:%d" % (self.hostname, self.port)
