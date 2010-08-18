import pycurl

from abstractclient import AbstractHTTPHeliosClient


class Client(AbstractHTTPHeliosClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        curl = pycurl.Curl()
        curl.setopt(pycurl.HTTPHEADER, ["Content-Type: application/json",
                                        "Connection: Keep-Alive"])
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.FORBID_REUSE, 0)
        curl.setopt(pycurl.VERBOSE, 0)
        curl.setopt(pycurl.NOPROGRESS, 1)
        curl.setopt(pycurl.FRESH_CONNECT, 0)
        # TODO: Increasing this definitely helps.  How high should we go?
        curl.setopt(pycurl.MAXCONNECTS, 20)
        curl.setopt(pycurl.WRITEFUNCTION, self.pycurl_write)
        # TODO: Tweak buffer sizes, timeouts, etc dynamically, etc?
        self.curl = curl

    def pycurl_write(self, data):
        pass

    def process_event(self, event):
        url, data = self.build_url_and_data(event)

        curl = self.curl
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POSTFIELDS, data)

        try:
            # self.curl_multi.add_handle(curl)
            curl.perform()
            return True
        except IOError:
            return False


client = Client()
client.start()
