from lib import Plugin
from lib.thirdparty import scrapemark
import re

class UrlCatcherPlugin(Plugin):
	def __init__(self):
		self.author = "Jim Persson"
		self.version = "1.0"
		        
		self.event.register_event('PRIVMSG', self.event_privmsg)

		self._re_url = re.compile('(https*\:\/\/[a-zA-Z0-9\/\?\&\=\.\%\-\_\,\~\:]*)')

	def event_privmsg(self, irc):
		match = self._re_url.search(irc.message.params)

		if not match:
			return

		url = match.group(0)
		data = scrapemark.scrape("<title>{{title}}</title>", url = url)

		if not data:
			return

		irc.reply('Title: %s' % data['title'])
