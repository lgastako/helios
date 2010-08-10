import logging
import threading
import time

from pymongo import Connection

from Queue import Queue

logger = logging.getLogger(__name__)


# TODO: Move to configuration later
MAX_INTERNAL_QUEUE_SIZE = 1000

# is instantiating at module import time bad?
_INTERNAL_QUEUE = Queue(maxsize=MAX_INTERNAL_QUEUE_SIZE)


def record(doctype, **kwargs):
    timestamp = time.time()
    _INTERNAL_QUEUE.put((timestamp, doctype, kwargs))


def internal_queue_size():
    return _INTERNAL_QUEUE.qsize()


def _get_connection():
    # TODO: Configurize
    conn = Connection('localhost', 27017)
    db = conn.helios_db
    return db


def _safe_get_connection():
    try:
        return _get_connection()
    except Exception:
        logger.exception("Could not get connection.")
        return None

def _post_event(conn, event):
    doctype, fields = event
    collection = getattr(conn, doctype)
    collection.insert(fields)
    return True


# TODO: Maybe decoratorize? e.g. @safe
def _safe_post_event(conn, event):
    try:
        return _post_event(conn, event)
    except Exception:
        logger.exception("Failed to log event: %s", event)
        return False


def _convert_to_postable_document(raw_event):
    timestamp, doctype, fields = raw_event
    event = {"ts": timestamp,
             "fields": fields}
    return doctype, event


def _process_queue():
    event = None
    conn = None
    while True:
        if not conn:
            conn = _safe_get_connection()
        if conn:
            if not event:
                raw_event = _INTERNAL_QUEUE.get()
                event = _convert_to_postable_document(raw_event)
            if _safe_post_event(conn, event):
                event = None
            else:
                conn = None
        else:
            # TODO: Implement incremental back-off and retry
            time.sleep(1)


_started = False

def _start():
    global _started
    if _started:
        return False
    _started = True
    # Fucking GIL.  Fuck python.
    thread = threading.Thread(target=_process_queue,
                              name="helios-queue-processor")
    thread.setDaemon(True)
    thread.start()
    return True


# ...if instantiating the queue at import is bad, this is probably
# REALLY bad :)
_start()
