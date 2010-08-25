from __future__ import unicode_literals

import json

from urllib import urlencode
from operator import itemgetter

from collections import defaultdict

from flask import Flask
from flask import render_template
from flask import request

from pymongo import Connection
from pymongo.code import Code

from pygments import highlight
from pygments.lexers import JavascriptLexer
from pygments.formatters import HtmlFormatter
from pygments.filter import Filter
from pygments.token import Token

app = Flask(__name__)


def safe_encode(value):
    # TODO: Make better later
    if value is None:
        return b"None"
    if isinstance(value, unicode):
        return value.encode("ascii")
    return value


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
    return rdoc["fields"]


def generate_link(key, value):
    return '?query={"%s"=%s}' % (key, value)


# class LinkingFilter(Filter):

#     def __init__(self, **options):
#         Filter.__init__(self, **options)

#     def filter(self, lexer, stream):
#         get_ready = False
#         for ttype, value in stream:
#             if get_ready and ttype is not Token.Text:
#                 get_ready = False
#                 value = "[HOLLA]%s[ENDHOLLA]" % value
#             if ((ttype is Token.Punctuation and value == "{") or
#                 (ttype is Token.Operator and value == ",")):
#                 get_ready = True
#             yield ttype, value


class LinkingHtmlFormatter(HtmlFormatter):

    # def wrap(self, source, outfile):
    #     yield 0, '<div class="highlight"><pre>'
    #     for i, t in source:
    #         if i == 1:
    #             # it's a line of formatted code
    #            import ipdb; ipdb.set_trace()
    #             t = t + '<br/>'
    #         yield i, t
    #     yield 0, '</pre></div>'

    def wrap(self, source, outfile):
        # overriding default behavior
        # P.S. I know outfile isn't referenced, this is the same as the
        # method I'm overriding.  hmmm.
        return self._wrap_div(self._wrap_pre(self._link_names(source)))

    def _link_names(self, source):
        for code_type, line in source:
            if code_type == 1:
                yield code_type, line
            else:
                yield code_type, line


def fancy_doc(doc, indent):
    # TODO: chardet is slow.  get rid of it.
    lexer = JavascriptLexer(encoding="chardet")
#    lexer.add_filter(LinkingFilter())
    if indent:
        code = json.dumps(doc, sort_keys=True, indent=4)
    else:
        code = json.dumps(doc, sort_keys=True)
    formatter = LinkingHtmlFormatter(nobackground=True)
#    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)


def do_collection_work(collection_name):
    #    limit = request.args.get("limit", DEFAULT_LIMIT)
    limit = 20
    offset = int(request.args.get("offset", 0))

    query = request.args.get("query", None)
    if query:
        adapted_query = adapt_query(json.loads(query))
    else:
        adapted_query = {}
    collection = getattr(get_mongo_db(), collection_name)
    raw_docs = collection.find(adapted_query).skip(offset).limit(limit)
    return locals()


@app.route("/col/<collection_name>")
def collection_view(collection_name):
    indent = False if request.args.get("indent") == "False" else True

# Dunno why this doesn't work, but ok, moving on...
#    locals().update(do_collection_work(collection_name))
    data = do_collection_work(collection_name)
    raw_docs = data["raw_docs"]
    collection = data["collection"]
    offset = data["offset"]
    limit = data["limit"]

    docs = [(rdoc["_id"],
             rdoc["ts"],
             fancy_doc(extract_fields(rdoc),
                       indent=indent))
            for rdoc in raw_docs]

    count = collection.count()

    next_offset = None
    prev_offset = None
    if count > offset + len(docs):
        next_offset = offset + limit
    if offset > 0:
        prev_offset = offset - limit

    data.update({"next_offset": next_offset,
                 "prev_offset": prev_offset,
                 "count": count,
                 "docs": docs,
                 "indent": indent})
    return render_template("collection.html", **data)


@app.route("/col/<collection_name>/chart")
def collection_chart_view(collection_name):
    data = do_collection_work(collection_name)
    values = defaultdict(list)
    for r in data["raw_docs"]:
        # TODO: If there are missing keys from some records, the chart
        # will be hosed.
        for key, value in r["fields"].items():
            values[key].append(value)
    def safe_float(x):
        return float(x or 0.0)
    def encode_values():
        mx = 0
        import sys
        mn = sys.maxint
        vlists = []
        for key, vlist in values.items():
            vlist = map(safe_float, vlist) # TODO: Fix
            vlists.append(",".join(map(unicode, vlist)))
            mx = max(mx, max(vlist))
            mn = min(mn, min(vlist))
        return mn, mx, "|".join(vlists)
    mn, mx, result_data = encode_values()
    data["chds"] = ",".join(map(unicode, [mn, mx]))
    data["result_data"] = result_data
    return render_template("post_chart.html", **data)


@app.route("/col/<collection_name>/mapreduce")
def collection_map_reduce_view(collection_name):
    collection = getattr(get_mongo_db(), collection_name)
    cursor = collection.find().limit(1)
    example_doc = list(cursor)[0]
    example_record = fancy_doc(extract_fields(example_doc), True)
    return render_template("mapreduce.html",
                           collection_name=collection_name,
                           example_record=example_record)


def generate_collection_query_link(result, base_path, group_by):
    params = {
        "query": json.dumps({
                safe_encode(group_by): safe_encode(result["_id"])})}
    return base_path + urlencode(params)


def augment_results_with_links(results, collection_name, group_by):
    base_path = "/col/" + collection_name + "?"
    new_results = []
    for result in results:
        link = generate_collection_query_link(result, base_path, group_by)
        new_results.append((link, result))
    return new_results


def do_count_work(collection_name):
    db = get_mongo_db()
    collection = getattr(db, collection_name)
    group_by = request.args.get("group_by")
    count = 0
    results = None
    reverse = request.args.get("reverse") == "True"
    if group_by:
        # TODO: Fix all the injection attacks like this.
        code = ("function() {\n"
                "    emit(this.fields.%s, 1)\n"
                "}\n") % group_by
        mapf = Code(code)
        reducef = Code("function(key, values) {\n"
                       "    var total = 0;\n"
                       "    for (var i=0; i<values.length; i++) {\n"
                       "        total += values[i];\n"
                       "    }\n"
                       "    return total;\n"
                       "}\n")
        results = list(collection.map_reduce(mapf, reducef).find())
        results.sort(key=itemgetter("value"), reverse=reverse)
        results = augment_results_with_links(results,
                                             collection_name,
                                             group_by)
    else:
        count = collection.count()

    return dict(collection_name=collection_name,
                count=count,
                group_by=group_by,
                results=results)


@app.route("/count/<collection_name>")
def count(collection_name):
    return render_template("count.html", **do_count_work(collection_name))


@app.route("/count/<collection_name>/chart")
def count_chart(collection_name):
    data = do_count_work(collection_name)
    values = [unicode(r[1]["value"])
              for r in data["results"]]
    data["result_data"] = ",".join(values)
    data["chds"] = ",".join([min(values), max(values)])
    return render_template("post_chart.html", **data)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/")
def home_view():
    db = get_mongo_db()
    counts = {}
    collection_names = list(db.collection_names())
    for col in collection_names:
        if col.startswith("system.") or col.startswith("tmp."):
            continue
        counts[col] = getattr(db, col).count()
    total = len(collection_names)
    return render_template("home.html",
                           total=total,
                           counts=counts)


if __name__ == "__main__":
    app.debug = True # TODO: optparseize
    app.run(host="0.0.0.0", port=5001)
