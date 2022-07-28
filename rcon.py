import socket
import time
from threading import Lock


class RCON:
    def __init__(self, server='localhost', password='password', port=27960, retries=3):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if ':' in server:
            self.server, self.port = server.split(":")
        else:
            self.server, self.port = server, port

        self.port = int(self.port)
        self.password = password
        self.last_cmd = None
        self.retries = retries  # default number of retries
        self.throttle_time = 0.0  # secs to wait between retries
        self.lock = Lock()

        self.socket.connect((self.server, self.port))
        self.socket.settimeout(0.75)

    def _send(self, data):
        ba = bytearray(b'\xFF\xFF\xFF\xFF')
        for c in f'{data}\n'.encode('ascii'):
            ba.append(c)
        self.socket.send(bytes(ba))

    def _recv(self):
        data = None
        try:
            data = self.socket.recv(4096)
        except socket.timeout:
            pass
        except socket.error:
            pass
        return data

    def _cmd(self, cmd):
        self.last_cmd = cmd
        retries = self.retries
        data = None

        while retries > 0 and data is None:
            self._send(cmd)
            data = self._recv()
            if data is None:
                time.sleep(self.throttle_time)
            retries -= 1

        return data[4:] if data is not None else data

    def rcon(self, cmd) -> str:
        """
        Send an rcon command, cmd
        """
        self.lock.acquire()
        reply = self._cmd('rcon "%s" %s' % (self.password, cmd))
        self.lock.release()
        return reply.decode('ascii', errors='ignore')

