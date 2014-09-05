from pyemitter import Emitter
from threading import Thread


class Source(Emitter):
    def __init__(self):
        self.thread = Thread(target=self.run)

    def start(self):
        self.thread.start()

    def run(self):
        pass
