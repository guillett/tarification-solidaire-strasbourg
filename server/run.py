import sys

sys.path.append("../technique")

from dotenv import load_dotenv

load_dotenv()
import os

from compute import compute

import datetime
from flask import jsonify, Flask, request
from flask_cors import CORS

application = Flask(__name__, static_folder="front/out", static_url_path="/")
CORS(application, origins="*")


@application.route("/")
def index():
    return application.send_static_file("index.html")


@application.route("/test")
def test():
    return application.send_static_file("test.html")


import json

from grist import api


@application.route("/fetch")
def fetch():
    scenario = request.args.get("scenario")
    qf = request.args.get("qf")

    (recettes, steps) = compute(scenario, qf)

    timestamp = datetime.datetime.now()
    api.add_records(
        "Scenarios_transports",
        [
            {
                "Date": timestamp.isoformat(),
                "Scenario": scenario,
                "Baremes": json.dumps(steps),
                "QF": qf,
                "Recettes": recettes[recettes.index == "50%"].recettes[0],
                "Ecart_type_recettes": recettes[recettes.index == "std"].recettes[0],
            },
        ],
    )

    html_table = recettes.to_html(
        float_format=lambda x: "{0:,.0f}".format(x).replace(",", " ")
    )
    return jsonify({"table": html_table})
