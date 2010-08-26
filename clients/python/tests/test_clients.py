from __future__ import unicode_literals

import json
import unittest

from time import time
from socket import gethostname

from mocker import Mocker

import abstractclient

from abstractclient import Event
from abstractclient import AbstractHeliosClient
from abstractclient import AbstractHTTPHeliosClient


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


class TestAbstractHeliosClient(unittest.TestCase):

    def setUp(self):
        self.client = AbstractHeliosClient()
        self.mocker = Mocker()
        self.time = self.mocker.mock()
        abstractclient.time = self.time

    def test_record_event_queues_event(self):
        event = "some event"
        self.client.record_event(event)
        self.assertEquals(1, self.client.queue.qsize())
        self.assertEquals(event, self.client.queue.get_nowait())

    def test_record_records_event_on_queue(self):
        # expect time request
        self.time()
        timestamp = time()
        # time request returns timestamp
        self.mocker.result(timestamp)
        args = {"some": "args",
                "of some kind": 1}
        event_type = "event type"

        with self.mocker:
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
