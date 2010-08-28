from __future__ import unicode_literals

import json
import unittest

from time import time
from socket import gethostname

from mocker import MockerTestCase

import abstractclient

from abstractclient import Event
from abstractclient import AbstractHeliosClient
from abstractclient import AbstractHTTPHeliosClient
from abstractclient import DEFAULT_VALUES


class TestEvent(unittest.TestCase):

    def test_from_json_constructs_event(self):
        timestamp = time()
        json_data = {"h": "homer",
                     "ts": timestamp,
                     "type": "event_type",
                     "args": ["some", "args"]}
        results = Event.from_json(json_data)
        self.assertTrue(results is not None)
        self.assertTrue(Event == type(results))
        self.assertTrue(timestamp == results.timestamp)
        self.assertTrue(json_data["type"] == results.event_type)
        self.assertTrue(json_data["args"] == results.args)
        self.assertTrue(json_data["h"] == results.hostname)


class NullClient(AbstractHeliosClient):

    def process_event(self):
        sleep(30)


class TestAbstractHeliosClient(MockerTestCase):

    def setUp(self):
        self.client = AbstractHeliosClient()

    def test_record_event_queues_event(self):
        event = "some event"
        self.client.record_event(event)
        self.assertEquals(1, self.client.queue.qsize())
        self.assertEquals(event, self.client.queue.get_nowait())

    def test_record_records_event_on_queue(self):
        timestamp = time()
        mock_time = self.mocker.replace("time.time")
        # expect time request
        mock_time()
        # time request returns timestamp
        self.mocker.result(timestamp)
        args = {"some": "args",
                "of some kind": 1}
        event_type = "event type"

        self.mocker.replay()
        self.client.record(event_type, **args)

        # verify results
        self.assertEquals(1, self.client.queue.qsize())
        event = self.client.queue.get_nowait()
        self.assertEquals(event_type, event.event_type)
        self.assertEquals(args, event.args)
        self.assertEquals(timestamp, event.timestamp)

    def test_qsize_returns_qsize(self):
        # duh
        self.assertEquals(0, self.client.qsize())
        self.client.queue.put(1)
        self.assertEquals(1, self.client.qsize())
        self.client.queue.put(2)
        self.assertEquals(2, self.client.qsize())
        self.client.queue.put(3)
        self.assertEquals(3, self.client.qsize())
        self.client.queue.get()
        self.assertEquals(2, self.client.qsize())
        self.client.queue.get()
        self.assertEquals(1, self.client.qsize())
        self.client.queue.get()
        self.assertEquals(0, self.client.qsize())

    def test_retry_event_enqueues_event(self):
        # duh
        self.assertEquals(0, self.client.qsize())
        self.client.retry_event(1)
        self.assertEquals(1, self.client.qsize())
        self.client.retry_event(1)
        self.assertEquals(2, self.client.qsize())
        self.client.retry_event(1)
        self.assertEquals(3, self.client.qsize())

    def test_process_queue_continues_until_process_is_set__to_false(self):
        """The client should continue until the process property
           is set to false...Which is never, btw."""

        def retry_event(event):
            self.client.process = False

        events = []
        def process_event(event):
            events.append(event)
            return event

        self.client.process_event = process_event
        self.client.retry_event = retry_event

        # Run three events, then stop
        self.client.queue.put(True)
        self.client.queue.put(True)
        self.client.queue.put(True)
        self.client.queue.put(False)

        self.client.process_queue()
        self.assertEquals([True, True, True, False], events)

    def test_start_does_nothing_if_started(self):
        # ensure no calls to threading.Thread
        self.mocker.replace("threading.Thread")
        # mock logging
        mock_logger = self.mocker.mock()
        self.mocker.result(mock_logger)
        # replace the logger
        abstractclient.logger = mock_logger
        # expect a call
        mock_logger.error("Already started.  Can't start again.")

        self.client.started = True
        self.mocker.replay()
        self.assertFalse(self.client.start())

    def test_start_starts_thread(self):
        # ensure calls to threading.Thread
        mock_threading = self.mocker.replace("threading.Thread")
        # mock logging
        mock_logger = self.mocker.mock()
        self.mocker.result(mock_logger)
        # replace the logger
        abstractclient.logger = mock_logger

        # expect threading call
        mock_threading(target=self.client.process_queue,
                       name="helios-queue-processor")
        self.mocker.result(mock_threading)

        mock_threading.setDaemon(True)
        mock_threading.start()

        self.mocker.replay()
        self.assertTrue(self.client.start())

    def test_queues_on_block(self):
        """The client should queue requests when the transport blocks."""

        client = NullClient()
        start = time()
        client.record("test")
        end = time()
        diff = end - start
        # Is this a good enough check to confirm that it's not blocking?
        self.assert_(diff < 0.01)
        self.assertEquals(1, client.qsize())

    def test_messages_exceeding_queue_size_are_dropped(self):
        FAKE_QUEUE_SIZE = 3

        try:
            original_max_qsize = abstractclient.DEFAULT_VALUES.MAX_QUEUE_SIZE
            abstractclient.DEFAULT_VALUES.MAX_QUEUE_SIZE = FAKE_QUEUE_SIZE

            client = NullClient()
            # Note: we intentionally don't .start() the client, so no
            # messages will be processed.

            for n in xrange(FAKE_QUEUE_SIZE):
                client.record("test", number=n)

            self.assertEquals(FAKE_QUEUE_SIZE, client.qsize())

            client.record("test", number=-1)

            self.assertEquals(FAKE_QUEUE_SIZE, client.qsize())

            for n in xrange(FAKE_QUEUE_SIZE):
                # I feel dirty touching the internals but don't know
                # a better way right now
                self.assertEqual(n, client.queue.get_nowait().args["number"])
            self.assertEquals(0, client.qsize())

        finally:
            abstractclient.DEFAULT_VALUES.MAX_QUEUE_SIZE = original_max_qsize

    # TODO: Add a test that when an event is dropped it is logged.


class TestAbstractHTTPHeliosClient(unittest.TestCase):

    def setUp(self):
        self.client = AbstractHTTPHeliosClient()

    def test_build_url_and_data_does_just_that(self):
        event = Event(timestamp=time(),
                      event_type="event type",
                      args=["my", "args"])
        hostname = gethostname()
        expected = {"h": hostname,
                    "ts": event.timestamp,
                    "type": event.event_type,
                    "args": event.args}
        url, data = self.client.build_url_and_data(event)
        self.assertEquals("http://localhost:2112/event/create", url)
        self.assertEquals(json.dumps(expected), data)


if __name__ == "__main__":
    unittest.main()
