# -*- coding: utf-8 -*-

from lib.plugin import Plugin
from lib.logger import Logger
from lib.thirdparty import scrapemark

import time

class RepostinatorPlugin(Plugin):
    def __init__(self):
        self.author = "Joel Söderberg"
        self.version = "0.1"

        self.event.register_system_event('urlcatcherurl', self.event_url)

    def event_url(self, params):
        (url, irc) = params;
        Logger.info("RepostinatorPlugin: Got url '%s' from urlcatcher" % params[0])
        if irc.server.get_current_nick() == irc.message.destination:
            Logger.debug("Got url in priv ignoring")
            return
        key = "%s_%s_%s" % (irc.message.destination, irc.get_ircnet_name(), url)
        data = self.store.get(key);
        if(data):
            irc.reply('This url was first posted in this channel by %s @ %s' % (data[0], data[2]))
        else:
            data = [irc.message.source.nick,  irc.message.destination, time.ctime()]
            self.store.put(key, data);