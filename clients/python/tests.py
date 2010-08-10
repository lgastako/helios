import unittest
import helios


class HeliosClientTests(unittest.TestCase):

    def test_helios_client_puts_request_on_internal_queue(self):
        pre_size = helios.internal_queue_size()
        helios.record("null_search",
                      query="bug free software")
        self.assertEquals(pre_size + 1, helios.internal_queue_size())


if __name__ == '__main__':
    unittest.main()
