import socket
import select
import threading

from lib import Logger

_SSL_ENABLED = True

try:
	import ssl
except ImportError:
	Logger.warning("Cannot import 'ssl'. SSL support will be disabled.")
	_SSL_ENABLED = False
	
#class ConnectionClosedException(Exception):
#	def __init__(self, reason = "Connection closed"):
#		Exception.__init__(self, reason)

class ConnectionFailedException(Exception):
	def __init__(self, reason = "Connection failed"):
		Exception.__init__(self, reason)
	
class AsyncBufferedNetSocket:
	##
	# @param server Hostname to connect to
	# @param port Port to use
	# @param use_ssl Whether to use SSL or not (only Python 2.6 or above)
	# @param use_ipv6 Wheher to use IPv6 or not
	# @param terminator Line terminator
	def __init__(self, server, port, use_ssl = False, use_ipv6 = False, terminator = "\n"):
		self.server = server
		self.port = port
		self.use_ssl = use_ssl
		self.use_ipv6 = use_ipv6
		self.terminator = terminator

		self.input_buffer = ""
		self.socket = None
		self.connected = False
		self.timeout = 1.0

		# Asynchronous callback methods
		self.OnConnect    = None
		self.OnDisconnect = None
		self.OnData       = None

		# Threads
		self.connection_thread = None

	##
	# Reader thread
	def thread_reader(self):
		while self.connected:
			line = self.read_line(timeout=1.0)

			if line and self.OnData:
				self.OnData(line, self)

		if self.OnDisconnect:
			self.OnDisconnect(self)

	def disconnect(self):
		self.connected = False
		self.connection_thread.join(timeout=10)

		if self.connection_thread.is_alive():
			Logger.warning("AsyncBufferedNetSocket: Thread did not exit")

		self.connection_thread = None

	##
	# Perform connection and start connection thread
	def connect(self):
		# Create socket
		sock = None

		if self.use_ipv6:
			sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
		else:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Connect the socket
		try:
			sock.connect((self.server, self.port))
		except:
			raise ConnectionFailedException()

		if self.use_ssl:
			if _SSL_ENABLED:
				sock = ssl.wrap_socket(sock)
			else:
				raise Exception("SSL is disabled")

		self.socket = sock
		self.connected = True

		if self.OnConnect:
			self.OnConnect(self)

		# Dispatch thread
		self.connection_thread = threading.Thread(target = self.thread_reader)
		self.connection_thread.start()

	## 
	# Read a line from the socket/buffer
	# @param timeout Maximum time in seconds to wait for data
	def read_line(self, timeout=0.0):
		if not self.connected:
			return None

		rlist = [self.socket]
		wlist = []
		xlist = []
		line = None

		# Maybe we already have something in the buffer
		pos = self.input_buffer.find(self.terminator)
		if pos != -1:
			line = self.input_buffer[:pos].strip()
			self.input_buffer = self.input_buffer[pos+1:]
			return line

		rsockets, wsockets, xsockets = select.select(rlist, wlist, xlist, timeout)

		if len(rsockets) > 0:
			try:
				data = rsockets[0].recv(4096)

				if Logger.is_debug():
					for line in data.splitlines():
						Logger.debug("RECV: " + line.strip())

			except:
				self.connected = False
				return

			# No data? We have been disconnected!
			if not data:
				self.connected = False
				return

			# Look for a terminator
			pos = data.find(self.terminator)
			if pos != -1:
				line = self.input_buffer + data[:pos].strip()
				self.input_buffer = data[pos+1:]
			else:
				self.input_buffer += data

		return line

	def send(self, data):
		Logger.debug("SEND: " + data.strip())
		self.socket.send(data)
