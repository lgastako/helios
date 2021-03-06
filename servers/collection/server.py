import optparse

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

app = Flask(__name__)

from abstractclient import Event
from helios_mongo import client as helios


@app.route("/event/create", methods=["POST"])
def create_event_view():
    json = request.json
    event = Event.from_json(request.json)
    helios.record_event(event)
    return jsonify(status="OK")


@app.route("/")
def home_view():
    return render_template("home.html")


def main():
    parser = optparse.OptionParser()
    parser.add_option("--listen-host", default="0.0.0.0")
    parser.add_option("--listen-port", default="5150")
    parser.add_option("-d", "--debug", action="store_true")
    options, args = parser.parse_args()

    if len(args) > 0:
        parser.error("Unexpected arguments: %s" % args)

    app.debug = options.debug
    app.run(host=options.listen_host, port=int(options.listen_port))


if __name__ == "__main__":
    main()
