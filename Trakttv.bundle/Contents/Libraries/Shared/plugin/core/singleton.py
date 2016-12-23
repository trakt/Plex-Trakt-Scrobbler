from plugin.core.environment import Environment

from SocketServer import TCPServer, StreamRequestHandler
from threading import Thread
import logging
import os
import socket
import time

log = logging.getLogger(__name__)

PORT_DEFAULT = 35374
PORT_PATH = os.path.join(Environment.path.plugin_data, 'Singleton')


def get_port():
    if not os.path.exists(PORT_PATH):
        return PORT_DEFAULT

    # Read data from file
    with open(PORT_PATH, 'r') as fp:
        data = fp.read()

    # Parse data
    try:
        return int(data.strip())
    except Exception as ex:
        log.warn('Unable to parse integer from %r: %s', PORT_PATH, ex, exc_info=True)
        return PORT_DEFAULT


class Singleton(object):
    host = '127.0.0.1'
    port = get_port()

    _server = None
    _thread = None

    @classmethod
    def acquire(cls):
        try:
            return cls._acquire()
        except Exception as ex:
            log.error('Exception raised in _acquire(): %s', ex, exc_info=True)
            return False

    @classmethod
    def _acquire(cls):
        # Start server
        if cls._start():
            return True

        # Attempt existing plugin shutdown
        if not cls.release():
            log.warn('Unable to shutdown existing plugin instance')
            return False

        # Try start server again
        return cls._start()

    @classmethod
    def release(cls):
        log.debug('Attempting to shutdown the existing plugin instance (port: %s)...', cls.port)

        # Request shutdown
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setblocking(0)
        client.settimeout(1.0)

        client.connect((cls.host, cls.port))

        client.sendall('shutdown\n')

        try:
            # Read response
            response = client.recv(128).strip()
        except socket.timeout:
            log.info('Release timeout', exc_info=True)
            return False

        if response != 'ok':
            log.info('Release failed: %r', response)
            return False

        log.info('Existing plugin instance has been shutdown')

        time.sleep(2)
        return True

    @classmethod
    def _start(cls):
        log.debug('Starting server (port: %s)...', cls.port)

        try:
            # Construct server
            cls._server = TCPServer((cls.host, cls.port), SingletonHandler)
        except socket.error as ex:
            if ex.errno != 10048:
                raise ex

            log.info('Plugin already running: %s', ex)
            return False

        # Start listening thread
        cls._thread = Thread(target=cls._run, name='Singleton')
        cls._thread.daemon = True

        cls._thread.start()

        log.debug('Started')
        return True

    @classmethod
    def _run(cls):
        try:
            cls._server.serve_forever()
        except Exception as ex:
            log.error('Server exception raised: %s', ex, exc_info=True)

        log.info('Server exited')


class SingletonHandler(StreamRequestHandler):
    def handle(self):
        try:
            self.process()
        except Exception as ex:
            log.error('Exception raised in process(): %s', ex, exc_info=True)

    def process(self):
        command = self.rfile.readline().strip()
        handler = getattr(self, 'on_%s' % (command, ), None)

        if handler is None:
            log.debug('Unknown command received: %r', command)
            return

        log.debug('Processing command: %r', command)

        try:
            handler()
        except Exception as ex:
            log.error('Handler raised an exception: %s', ex, exc_info=True)

    def on_shutdown(self):
        self.wfile.write('ok\n')

        log.info('Exit')
        os._exit(1)
