import logging
import optparse
import time

import json

from helios_mongo import client as mongo_client
from helios_urllib2 import client as urllib2_client
from helios_pycurl import client as pycurl_client
from helios_pycurl import client as urlgrabber_client


def build_client_map():
    client_map = {}
    for key in globals():
        if key.endswith("_client"):
            prefix = key[:-len("_client")]
            client_map[prefix] = globals()[key]
    return client_map


CLIENTS = build_client_map()


def run_example(client, delay, values, quit_after_secs):
    start = None
    if not values:
        values = {}
    if quit_after_secs:
        start = time.time()
    count = 0
    while True:
        timestamp = time.time()
        print "Recording event with timestamp: %s" % timestamp
        print "Queue size: %s" % client.qsize()
        kwargs = {"app_timestamp": timestamp}
        kwargs.update(values)
        client.record("clock_tick", **kwargs)
        time.sleep(delay)
        count += 1
        if quit_after_secs and start and time.time() - start > quit_after_secs:
            break
    return count


def main():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--delay", default="1")
    parser.add_option("-j", "--json", help="specify JSON to be added to event")
    parser.add_option("--debug", action="store_true")
    parser.add_option("--quit-after-secs", default="0")
    parser.add_option("--client", default="urllib2")
    options, args = parser.parse_args()

    if len(args) > 0:
        parser.error("I got no beef with you.")

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    delay = float(options.delay)
    quit_after_secs = float(options.quit_after_secs)
    values = None
    if options.json:
        values = json.loads(options.json)

    client = CLIENTS[options.client]
    start = time.time()
    count = run_example(client, delay, values, quit_after_secs)
    diff = time.time() - start
    qps = float(count) / diff

    print "Posted %d events in %d seconds for %0.2f qps" % (count,
                                                            diff,
                                                            qps)

if __name__ == '__main__':
    main()
