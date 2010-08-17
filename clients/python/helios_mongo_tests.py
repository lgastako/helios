import unittest

from helios_mongo import client as helios


class HeliosClientTests(unittest.TestCase):

    def test_helios_client_puts_request_on_internal_queue(self):
        pre_size = helios.qsize()
        helios.record("null_search",
                      query="bug free software")
        self.assertEquals(pre_size + 1, helios.qsize())


if __name__ == '__main__':
    unittest.main()
