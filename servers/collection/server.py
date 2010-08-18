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


if __name__ == "__main__":
    app.debug = True # TODO: optparseize
    app.run()
