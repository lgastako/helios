import urllib2

from abstractclient import AbstractHTTPHeliosClient


class Client(AbstractHTTPHeliosClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

    def process_event(self, event):
        url = self.build_url(event)
        urllib2.open(url)
