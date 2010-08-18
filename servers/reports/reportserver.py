import json

from flask import Flask
from flask import render_template
from flask import request

from pymongo import Connection

app = Flask(__name__)


def get_mongo_db():
    # TODO: Figure out strategy for getting mongo connections instead
    # of per-view.
    conn = Connection('localhost', 27017)
    db = conn.helios_db
    return db


def remove_id(doc):
    del doc["_id"]
    return doc


def adapt_query(query):
    for key, value in query.items():
        del query[key]
        query["fields." + key] = value
    return query


def extract_fields(rdoc):
    if not "fields" in rdoc:
        return None
    return json.dumps(rdoc["fields"])


@app.route("/col/<collection_name>")
def collection_view(collection_name):
#    limit = request.args.get("limit", DEFAULT_LIMIT)
    limit = 20
    offset = int(request.args.get("offset", 0))
    query = request.args.get("query", None)
    if query:
        query = adapt_query(json.loads(query))
    else:
        query = {}
    db = get_mongo_db()
    collection = getattr(db, collection_name)
    raw_docs = collection.find(query).skip(offset).limit(limit)
    docs = [(rdoc["_id"], rdoc["ts"], extract_fields(rdoc))
            for rdoc in raw_docs]
    count = collection.count()
    next_offset = None
    prev_offset = None
    if count > offset + len(docs):
        next_offset = offset + limit
    if offset > 0:
        prev_offset = offset - limit
    return render_template("collection.html",
                           docs=docs,
                           collection_name=collection_name,
                           offset=offset,
                           next_offset=next_offset,
                           prev_offset=prev_offset,
                           count=count,
                           limit=limit)


@app.route("/")
def home_view():
    db = get_mongo_db()
    counts = {}
    for col in db.collection_names():
        if col.startswith("system."):
            continue
        counts[col] = getattr(db, col).count()
    return render_template("home.html",
                           counts=counts)


if __name__ == "__main__":
    app.debug = True # TODO: optparseize
    app.run(port=5001)
