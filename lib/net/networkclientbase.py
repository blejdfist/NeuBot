import socket
import select
import threading
import ssl

class NetworkClientError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class ConnectionFailedError(NetworkClientError):
    pass

class DisconnectFailedError(NetworkClientError):
    pass

class ConnectionLostError(NetworkClientError):
    pass

class BufferedNetworkClientBase(object):
    def __init__(self):
        # Settings
        self._line_separators = ["\r", "\n"]
        self._terminator = "\n"

        # State
        self._is_connected = False
        self._socket = None
        self._input_buffer = ""
        self._reader_thread = None

    def handle_connected(self):
        pass

    def handle_error(self, e):
        pass

    def handle_disconnected(self):
        pass

    def handle_data(self, data):
        pass

    def connect(self, host, port, use_ssl = False, use_ipv6 = False):
        # Create socket
        sock = None

        if use_ipv6:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket
        try:
            sock.connect((host, port))
        except socket.error as e:
            raise ConnectionFailedError("Connection failed: " + str(e))

        if use_ssl:
            sock = ssl.wrap_socket(sock)

        self._socket = sock
        self._is_connected = True

        self.handle_connected()

        # Dispatch thread
        self._reader_thread = threading.Thread(target = self._thread_reader)
        self._reader_thread.start()

    def disconnect(self):
        self._is_connected = False

        if self._reader_thread:
            self._reader_thread.join(timeout=10)

            if self._reader_thread.is_alive():
                raise DisconnectFailedError("Timeout when joining waiting for reader thread")

        self._reader_thread = None

    def _read_line(self, timeout=0.0):
        if not self._is_connected:
            return None

        rlist = [self._socket]
        wlist = []
        xlist = []
        line = None

        # Maybe we already have something in the buffer
        pos = self._input_buffer.find(self._terminator)
        if pos != -1:
            line = self._input_buffer[:pos].strip()
            self._input_buffer = self._input_buffer[pos+1:]
            return line

        rsockets, wsockets, xsockets = select.select(rlist, wlist, xlist, timeout)

        if len(rsockets) > 0:
            try:
                data = rsockets[0].recv(4096)

            except:
                self._is_connected = False
                raise ConnectionLostError("Connection lost during read")

            # No data? We have been disconnected!
            if not data:
                self._is_connected = False
                raise ConnectionLostError("Connection lost during read. No data.")

            # Look for a terminator
            pos = data.find(self._terminator)
            if pos != -1:
                line = self._input_buffer + data[:pos].strip()
                self._input_buffer = data[pos+1:]
            else:
                self._input_buffer += data

        return line

    def send(self, data):
        try:
            self._socket.send(data)
        except socket.error as e:
            self._is_connected = False
            raise ConnectionLostError("Connection lost during send")

    def _thread_reader(self):
        while self._is_connected:
            try:
                line = self._read_line(timeout=1.0)

                if line:
                    self.handle_data(line)

            except NetworkClientError as e:
                self.handle_error(e)

        self.handle_disconnected()
