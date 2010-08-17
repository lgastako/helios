"""Tests for the generic python client which is transport-independent."""

import unittest

from time import sleep
from time import time

from abstractclient import AbstractHeliosClient


class NullClient(AbstractHeliosClient):

    def process_queue(self):
        while True:
            sleep(30)


class AbstractHeliosClientTests(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
