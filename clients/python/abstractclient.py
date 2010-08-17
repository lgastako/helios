import logging
import threading

from Queue import Queue
from time import time

logger = logging.getLogger(__name__)


class Event(object):

    def __init__(self, timestamp=None, event_type=None, args=None):
        self.timestamp = timestamp
        self.event_type = event_type
        self.args = args


class AbstractHeliosClient(object):

    def __init__(self):
        self.queue = Queue()
        self.started = False

    def record(self, event, **kwargs):
        timestamp = time()
        self.queue.put(Event(timestamp=timestamp,
                             event_type=event,
                             args=kwargs))

    def qsize(self):
        return self.queue.qsize()

    def retry_event(self, event):
        # For now we just throw it back on the queue... ultimately we should
        # figure out ordering and/or priorities.
        self.queue.put(event)

    def process_queue(self):
        logger.debug("process_queue started.")
        # TODO: Error handling, incremental backoff/retry, etc.
        while True:
            event = self.queue.get()
            if not self.process_event(event):
                self.retry_event(event)

    def process_event(self, event):
        raise NotImplementedError

    def start(self):
        if self.started:
            logger.error("Already started.  Can't start again.")
            return False

        self.started = True

        # Fucking GIL.  Fuck python.
        thread = threading.Thread(target=self.process_queue,
                                  name="helios-queue-processor")
        thread.setDaemon(True)
        thread.start()
        return True


class AbstractHTTPHeliosClient(AbstractHeliosClient):

    def build_url(self, event):
        if True:
            raise Exception("Not Implemented")
