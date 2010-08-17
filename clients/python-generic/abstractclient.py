from Queue import Queue
from time import time


class Event(object):

    def __init__(self, timestamp=None, event_type=None, args=None):
        self.timestamp = timestamp
        self.event_type = event_type
        self.args = args


class AbstractHeliosClient(object):

    def __init__(self):
        self.queue = Queue()

    def record(self, event, **kwargs):
        timestamp = time()
        self.queue.put(Event(timestamp=timestamp,
                             event_type=event,
                             args=kwargs))

    def qsize(self):
        return self.queue.qsize()

    def process_queue(self):
        while True:
            event = self.queue.get()
            self.process_event(event)

    def process_event(self):
        raise NotImplementedError


class AbstractHTTPHeliosClient(AbstractHeliosClient):

    def build_url(self, event):
        raise NotImplementedError
