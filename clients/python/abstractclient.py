import logging
import threading

from Queue import Queue
from time import time
from socket import gethostname

import json

logger = logging.getLogger(__name__)

HOSTNAME = gethostname()


class Event(object):

    def __init__(self, hostname=None, timestamp=None, event_type=None,
                 args=None):
        if hostname is None:
            hostname = HOSTNAME
        self.hostname = hostname
        self.timestamp = timestamp
        self.event_type = event_type
        self.args = args

    @classmethod
    def from_json(cls, json_data):
        return cls(hostname=json_data["h"],
                   timestamp=json_data["ts"],
                   event_type=json_data["type"],
                   args=json_data["args"])


class AbstractHeliosClient(object):

    def __init__(self):
        self.queue = Queue()
        self.started = False

    def record_event(self, event):
        self.queue.put(event)

    def record(self, event_type, **kwargs):
        timestamp = time()
        event = Event(timestamp=timestamp,
                      event_type=event_type,
                      args=kwargs)
        self.record_event(event)

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

        # This is questionable as daemon threads get killed when other
        # threads end, so we will lose data here.  I can't find a way
        # to let daemon threads do cleanup.... maybe we could make it
        # non-daemonic and have it keep checking for existence of
        # other non-daemon threads and when there are no more then it
        # suicides, but thats lame and probably hard to do while
        # staying fast.
        # Maybe we can use atexit?
        thread.setDaemon(True)

        thread.start()
        return True

    def main(self, name):
        if name != "__main__":
            return
        import optparse
        parser = optparse.OptionParser()
        options, args = parser.parse_args()

        if not 0 < len(args) < 3:
            parser.error("Must supply exactly one event type and"
                         " optionally one JSON data structure.")

        event_type = args[0]
        if len(args) > 1:
            json_data = args[1]
            try:
                data = json.loads(json_data)
            except Exception:
                parser.error("Could not parse JSON")
        else:
            data = {}
        self.record(event_type, **data)
        #print "Recorded event: %s (%s)" % (event_type, data)
        # This needs to be removed but for now is necessary to make sure
        # everything gets flushed
        import time
        time.sleep(1)


class AbstractHTTPHeliosClient(AbstractHeliosClient):

    def _build_url(self):
        # TODO: Configurize
        return "http://localhost:2112/event/create"

    def _build_data(self, event):
        data = {"h": event.hostname,
                "ts": event.timestamp,
                "type": event.event_type,
                "args": event.args}
        return json.dumps(data)

    def build_url_and_data(self, event):
        url = self._build_url()
        data = self._build_data(event)
        return url, data
