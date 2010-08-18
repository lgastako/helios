from urlgrabber import urlopen

from abstractclient import AbstractHTTPHeliosClient


class Client(AbstractHTTPHeliosClient):

    def process_event(self, event):
        url, data = self.build_url_and_data(event)
        headers = {"Content-Type": "application/json"}
        try:
            urlopen(url, data=data, http_headers=headers.items())
            return True
        except IOError:
            return False


client = Client()
client.start()
