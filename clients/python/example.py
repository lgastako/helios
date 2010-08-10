import logging
import optparse
import time

import json

import helios


def run_example(delay, values, quit_after_secs):
    start = None
    if not values:
        values = {}
    if quit_after_secs:
        start = time.time()
    while True:
        timestamp = time.time()
        print "Recording event with timestamp: %s" % timestamp
        print "Queue size: %s" % helios.internal_queue_size()
        kwargs = {"app_timestamp": timestamp}
        kwargs.update(values)
        helios.record("clock_tick", **kwargs)
        time.sleep(delay)
        if start and time.time() - start > quit_after_secs:
            break


def main():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--delay", default="1")
    parser.add_option("-j", "--json", help="specify JSON to be added to event")
    parser.add_option("--debug", action="store_true")
    parser.add_option("--quit-after-secs")
    options, args = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG)

    delay = float(options.delay)
    quit_after_secs = float(options.quit_after_secs)
    values = None
    if options.json:
        values = json.loads(options.json)
    run_example(delay, values, quit_after_secs)


if __name__ == '__main__':
    main()
