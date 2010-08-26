import optparse

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request


class MyFlask(Flask):

    def __init__(self, *args, **kwargs):
        super(MyFlask, self).__init__(*args, **kwargs)
        self.remote_host = None
        self.remote_port = None


app = MyFlask(__name__)

from abstractclient import Event
from helios_pycurl import client as helios

# TODO: Un-ghetto-ize
helios._build_url = lambda: "http://localhost:5150/event/create"


@app.route("/event/create", methods=["POST"])
def create_event_view():
    event = Event.from_json(request.json)
    import ipdb; ipdb.set_trace()
    helios.record_event(event)
    return jsonify(status="OK")


@app.route("/")
def home_view():
    return render_template("home.html")


def main():
    parser = optparse.OptionParser()
    parser.add_option("-s", "--remote-server", default="localhost")
    parser.add_option("-p", "--remote-port", default="5150")
    parser.add_option("--listen-host", default="0.0.0.0")
    parser.add_option("--listen-port", default="2112")
    parser.add_option("-d", "--debug", action="store_true")
    options, args = parser.parse_args()

    if len(args) > 0:
        parser.error("Unexpected arguments: %s" % args)

    app.debug = options.debug
    app.remote_host = options.remote_server
    app.remote_port = int(options.remote_port)
    app.run(host=options.listen_host, port=int(options.listen_port))


if __name__ == "__main__":
    main()
