from lib.logger import Logger

import threading

##
# @class IRCCommandDispatcher
# Simplifies handling of irc command return codes
class IRCCommandDispatcher:
	def __init__(self, irccontroller, eventcontroller):
		self.eventcontroller = eventcontroller
		self.irccontroller = irccontroller
		self.event = None
		self.success = False

	def event_failed(self, irc):
		self.success = False
		self.event.set()

	def event_success(self, irc):
		self.success = True
		self.event.set()

	##
	# Send a command and block execution until a response code is seen
	# @param cmd Raw command to send
	# @param success_codes Array of server return codes that signal a success
	# @param failure_codes Array of server return codes that signal failure
	# @param timeout Maximum time in seconds to wait for a return code
	def send_command_and_wait(self, cmd, success_codes = None, failure_codes = None, timeout = 60):
		if failure_codes is None:
			raise Exception("Need to specify failure codes")

		if success_codes is None:
			raise Exception("Need to specify success codes")

		for code in failure_codes:
			self.eventcontroller.register_event(code, self.event_failed)

		for code in success_codes:
			self.eventcontroller.register_event(code, self.event_success)

		self.event = threading.Event()
		self.irccontroller.send_raw(cmd)
		self.event.wait(timeout)

		self.eventcontroller.release_related(self)

		if not self.event.is_set():
			Logger.debug("Command timed out")
			return False

		if self.success:
			Logger.debug("Command was successful")
			return True
		
		Logger.debug("Command failed")
		return False
