from SocketServer import TCPServer, StreamRequestHandler
from threading import Thread
import logging
import os
import socket
import time

log = logging.getLogger(__name__)


class Singleton(object):
    port = 35374

    _server = None
    _thread = None

    @classmethod
    def acquire(cls):
        # Start singleton server
        if cls._start():
            return True

        # Attempt existing plugin shutdown
        if not cls.release():
            log.warn('Unable to shutdown existing plugin instance')
            return False

        # Try start singleton server
        return cls._start()

    @classmethod
    def release(cls):
        log.debug('Attempting to shutdown the existing plugin instance...')

        # Request shutdown
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', cls.port))

        client.sendall('shutdown\n')

        # Read response
        response = client.recv(128).strip()

        if response != 'OK':
            return False

        log.info('Existing plugin instance has been shutdown')

        time.sleep(2)
        return True

    @classmethod
    def _start(cls):
        log.debug('Starting singleton server...')

        try:
            # Construct server
            cls._server = TCPServer(('127.0.0.1', cls.port), SingletonHandler)
        except socket.error, ex:
            if ex.errno != 10048:
                raise ex

            log.info('Plugin already running: %s', ex)
            return False

        # Start listening thread
        cls._thread = Thread(target=cls._run, name='Singleton')
        cls._thread.start()

        log.debug('Started')
        return True

    @classmethod
    def _run(cls):
        try:
            cls._server.serve_forever()
        except Exception, ex:
            log.warn('Server exception raised: %s', ex, exc_info=True)

        log.info('Server exited')


class SingletonHandler(StreamRequestHandler):
    def handle(self):
        try:
            self.process()
        except Exception, ex:
            log.warn('Exception raised in process(): %s', ex, exc_info=True)

    def process(self):
        command = self.rfile.readline().strip()
        handler = getattr(self, 'on_%s' % (command, ), None)

        if handler is None:
            log.debug('Unknown command received: %r', command)
            return

        log.debug('Processing command: %r', command)

        try:
            handler()
        except Exception, ex:
            log.warn('Handler raised an exception: %s', ex, exc_info=True)

    def on_shutdown(self):
        # TODO ensure another plugin process exists

        self.wfile.write('OK\n')

        log.info('Exit')
        os._exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    Singleton.acquire()
