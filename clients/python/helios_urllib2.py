from urllib2 import urlopen
from urllib2 import Request

from abstractclient import AbstractHTTPHeliosClient


class Client(AbstractHTTPHeliosClient):

    def process_event(self, event):
        url, data = self.build_url_and_data(event)
        headers = {"Content-Type": "application/json"}
        request = Request(url, data, headers)
        urlopen(request)
        return True


client = Client()
client.start()
