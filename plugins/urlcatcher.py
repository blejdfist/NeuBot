from lib.plugin import Plugin
from lib.logger import Logger
from lib.thirdparty import scrapemark

import re
import urlparse

class UrlCatcherPlugin(Plugin):
    def __init__(self):
        self.author = "Jim Persson"
        self.version = "1.0"

        self.event.register_event('PRIVMSG', self.event_privmsg)

        self._re_url = re.compile(r"(https*\:\/\/[^ \t]*)")

    def event_privmsg(self, irc):
        match = self._re_url.search(irc.message.params)

        if not match:
            return

        url = match.group(0)
        res = urlparse.urlsplit(url)

        # Don't try to get the title for ftp etc
        if res.scheme not in ['http', 'https']:
            return

        # Encode domain part to IDNA if possible
        netloc = res.netloc
        try:
            hostname = res.hostname.encode('IDNA')

            # Add back the username and password
            if '@' in netloc:
                usernpass, _ = netloc.rsplit('@')
                netloc = usernpass + '@' + hostname
            else:
                netloc = hostname
        except:
            pass

        res = res._replace(fragment = '', netloc = netloc)

        # Reassemble the parts
        url = urlparse.urlunsplit(res)
        self.event.dispatch_system_event('urlcatcherurl', [url, irc])

        Logger.info("Urlcatcher retrieving '%s'" % url)
        try:
            data = scrapemark.scrape("<title>{{title}}</title>", url = url)

            if not data:
                Logger.info("Urlcatcher received no title")
                return

            irc.reply('Title: %s' % data['title'])
        except Exception, e:
            Logger.warning("Urlcatcher error")
            raise e
