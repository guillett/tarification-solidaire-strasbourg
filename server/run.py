import sys

sys.path.append("../technique")

from dotenv import load_dotenv

load_dotenv()
import datetime
import os
from openfisca_france import CountryTaxBenefitSystem

# from compute import compute
from flask import jsonify, Flask, request, redirect, send_file, session
from flask_cors import CORS

application = Flask(__name__, static_folder="front/out", static_url_path="/")
application.secret_key = os.getenv("SECRET_KEY")
CORS(application, origins="*")

client_id = os.getenv("OAUTH_CLIENT_ID")
client_secret = os.getenv("OAUTH_CLIENT_SECRET")
oauth_authorize_url = os.getenv("OAUTH_AUTHORIZE_URL")
oauth_logout_url = os.getenv("OAUTH_LOGOUT_URL")
oauth_token_url = os.getenv("OAUTH_TOKEN_URL")
oauth_userinfo_url = os.getenv("OAUTH_USERINFO_URL")

BASE_URL = os.getenv("BASE_URL")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

base = CountryTaxBenefitSystem()
base.load_extension("openfisca_france_local")


def get_timestamp():
    return datetime.datetime.now().isoformat().replace(":", "-")[0:19]


@application.route("/")
def index():
    return application.send_static_file("index.html")


import urllib.parse


@application.route("/login")
def login():
    url = f"{oauth_authorize_url}?"
    params = {
        "client_id": client_id,
        "state": "42",
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": f"{BASE_URL}/auth",
    }

    full_path = url + urllib.parse.urlencode(params)
    return redirect(full_path)


@application.route("/logout")
def logout():
    url = f"{oauth_logout_url}?"
    params = {
        "post_logout_redirect_uri": f"{BASE_URL}/",
        "id_token_hint": session["id_token"] if "id_token" in session else None,
    }

    full_path = url + urllib.parse.urlencode(params)
    if "email" in session:
        session.pop("email")
    return redirect(full_path)


import requests


@application.route("/auth")
def auth():
    code = request.args.get("code")
    access_token_url = oauth_token_url
    params = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": f"{BASE_URL}/auth",
    }
    res_token = requests.post(
        access_token_url, data=params, headers={"accept": "application/json"}
    )
    res_token_json = res_token.json()
    token = res_token_json["access_token"]
    res_info = requests.get(
        oauth_userinfo_url, headers={"authorization": f"bearer {token}"}
    )
    session["id_token"] = res_token_json["id_token"]

    email = res_info.json()["email"]
    login = email[0 : email.find("@")]
    session["email"] = email

    timestamp = get_timestamp()
    log_file = f"{UPLOAD_FOLDER}.connexions/{timestamp}_{login}"
    with open(log_file, "w") as f:
        pass

    return redirect("/")


@application.route("/me")
def me():
    if "email" in session:
        return jsonify({"email": session["email"]})
    else:
        return jsonify({"error": "not logged in"}), 401


AUTORIZED_EMAILS = os.getenv("AUTORIZED_EMAILS", "").split(",")


def get_files():
    files = [
        {"name": f.name, "size": round(f.stat().st_size / 1000000, 3)}
        for f in os.scandir(UPLOAD_FOLDER)
        if not f.name.startswith(".")
    ]
    files.sort(key=lambda i: i["name"])
    return files


@application.route("/files", methods=["GET", "POST"])
def files():
    if "email" not in session or session["email"] not in AUTORIZED_EMAILS:
        if os.getenv("FLASK_DEBUG") != "1":
            return jsonify({"error": "unautorized"}), 403

    file_data = get_files()
    if request.method == "POST":
        name = request.form["name"]
        file_names = [f["name"] for f in file_data]
        if name in file_names:
            file_path = f"{UPLOAD_FOLDER}/{name}"
            return send_file(file_path)
    else:
        return jsonify(file_data)


def get_login():
    if os.getenv("FLASK_DEBUG") == "1":
        return "thomas"

    if "email" in session:
        email = session["email"]
        if email.endswith("@strasbourg.eu") or email == "thomas@codeursenliberte.fr":
            return email[0 : email.find("@")]
        raise Exception(f"Wrong email, no chocolate ({email})")
    raise Exception("No email, no chocolate")


from scenario import process_file_sheets

sys.path.append("../culture")
from centre_choregraphique import get_results as centre_choregraphique_get_results
from conservatoire import get_results as conservatoire_get_results

sys.path.append("../sports")
from sports import get_results as sports_get_results

sys.path.append("../mobilite")
from mobilite import server_get_results as mobilite_get_results

sys.path.append("../dee")
from dee import get_results as dee_get_results

get_results_fncs = {
    "ccs": centre_choregraphique_get_results,
    "crr": conservatoire_get_results,
    "cts": mobilite_get_results,
    "dee": dee_get_results,
    "sports": sports_get_results,
}


@application.route("/budget", methods=["POST"])
def budget():
    subject = request.form["subject"]
    source = request.form["source"]
    adjustment = request.form["adjustment"]
    timestamp = get_timestamp()
    login = get_login()

    if (
        subject not in ["ccs", "cts", "sports", "dee", "crr"]
        or source not in ["caf", "insee", "caf_insee_complete"]
        or adjustment not in ["v1", "v2", "v3", "v4"]
    ):
        return jsonify({"error": "incorrect data"}), 500

    if subject not in get_results_fncs:
        raise Exception(f"Oupsy. {subject}")

    if "file" in request.files:
        f = request.files["file"]
        file_id = f"{subject}_{source}_{adjustment}_{timestamp}_{login}"
        input_filename = f"{UPLOAD_FOLDER}/baremes_{file_id}.ods"
        f.save(input_filename)

        fd = os.open(input_filename, os.O_RDONLY)
        size = os.fstat(fd).st_size
        os.close(fd)

        if size == 0:
            input_filename = None
    else:
        input_filename = None

    output_filename = f"{UPLOAD_FOLDER}/resultats_{file_id}.xlsx"
    get_results_fnc = get_results_fncs[subject]
    process_file_sheets(
        base,
        subject,
        source,
        adjustment,
        get_results_fnc,
        input_filename,
        output_filename,
    )

    return send_file(output_filename)


from baremes import build_sheet


@application.route("/template", methods=["POST"])
def template():
    subject = request.form["subject"]
    timestamp = get_timestamp()
    login = get_login()

    file_path = f"{UPLOAD_FOLDER}/{subject}_{timestamp}_{login}.ods"
    build_sheet(base, subject, file_path)
    return send_file(file_path)


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
