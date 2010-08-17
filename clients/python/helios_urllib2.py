from urllib2 import urlopen

from abstractclient import AbstractHTTPHeliosClient


class Client(AbstractHTTPHeliosClient):

    def process_event(self, event):
        url = self.build_url(event)
        urlopen(url)


client = Client()
client.start()
