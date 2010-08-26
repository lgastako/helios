import logging
import threading

from pymongo import Connection

from Queue import Queue

from abstractclient import AbstractHeliosClient

logger = logging.getLogger(__name__)


# TODO: Move to configuration later
MAX_INTERNAL_QUEUE_SIZE = 1000

# is instantiating at module import time bad?
_INTERNAL_QUEUE = Queue(maxsize=MAX_INTERNAL_QUEUE_SIZE)


class Client(AbstractHeliosClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        # TODO: Configurize
        # TODO: Replace with a connection that replaces it self on failures
        # etc.
        self.conn = Connection("localhost", 27017)
        self.db = self.conn.helios_db

    def process_event(self, event):
        collection = getattr(self.db, event.event_type)
        collection.insert(self._convert_event(event))
        return True

    def _convert_event(self, event):
        """Converts an event to a document postable to mongo."""

        doc = {"h": event.hostname,
               "ts": event.timestamp}
        if event.args:
            doc["fields"] = event.args
        return doc


# ...if instantiating the queue at import is bad, this is probably
# REALLY bad since it kicks of a thread, etc. but we'll see how it
# goes.
client = Client()
client.start()
client.main(__name__)
