import logging
import optparse
import time

import json

import helios


def run_example(delay, values=None):
    if not values:
        values = {}
    while True:
        timestamp = time.time()
        print "Recording event with timestamp: %s" % timestamp
        print "Queue size: %s" % helios.internal_queue_size()
        kwargs = {"app_timestamp": timestamp}
        kwargs.update(values)
        helios.record("clock_tick", **kwargs)
        time.sleep(delay)


def main():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--delay", default="1")
    parser.add_option("-j", "--json", help="specify JSON to be added to event")
    parser.add_option("--debug", action="store_true")
    options, args = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    delay = int(options.delay)
    values = None
    if options.json:
        values = json.loads(options.json)
    run_example(delay, values)


if __name__ == '__main__':
    main()
