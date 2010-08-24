from __future__ import unicode_literals

import json

from urllib import urlencode

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
    formatter = LinkingHtmlFormatter()
#    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)


@app.route("/col/<collection_name>")
def collection_view(collection_name):
#    limit = request.args.get("limit", DEFAULT_LIMIT)
    limit = 20
    offset = int(request.args.get("offset", 0))
    indent = True if request.args.get("indent") == "True" else False

    query = request.args.get("query", None)
    if query:
        query = adapt_query(json.loads(query))
    else:
        query = {}
    db = get_mongo_db()
    collection = getattr(db, collection_name)
    raw_docs = collection.find(query).skip(offset).limit(limit)
    docs = [(rdoc["_id"], rdoc["ts"], fancy_doc(extract_fields(rdoc),
                                                indent=indent))
            for rdoc in raw_docs]
    count = collection.count()
    next_offset = None
    prev_offset = None
    if count > offset + len(docs):
        next_offset = offset + limit
    if offset > 0:
        prev_offset = offset - limit
    pygments_css = HtmlFormatter().get_style_defs('.highlight')

    return render_template("collection.html",
                           docs=docs,
                           collection_name=collection_name,
                           offset=offset,
                           next_offset=next_offset,
                           prev_offset=prev_offset,
                           count=count,
                           limit=limit,
                           pygments_css=pygments_css,
                           indent=indent)


def safe_encode(value):
    # TODO: Make better later
    if value is None:
        return b"None"
    if isinstance(value, unicode):
        return value.encode("ascii")
    return value


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


@app.route("/count/<collection_name>")
def count(collection_name):
    db = get_mongo_db()
    collection = getattr(db, collection_name)
    group_by = request.args.get("group_by")
    count = 0
    results = None
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
        results = collection.map_reduce(mapf, reducef).find()
        results = augment_results_with_links(results,
                                             collection_name,
                                             group_by)
    else:
        count = collection.count()
    return render_template("count.html",
                           collection_name=collection_name,
                           count=count,
                           group_by=group_by,
                           results=results)


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
