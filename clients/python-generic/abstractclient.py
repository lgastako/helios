from Queue import Queue
from time import time


class AbstractHeliosClient(object):

    def __init__(self):
        self.queue = Queue()

    def record(self, event, **kwargs):
        timestamp = time()
        self.queue.put((timestamp, event, kwargs))

    def qsize(self):
        return self.queue.qsize()

    def process_queue(self):
        raise NotImplementedError
