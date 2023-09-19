import sys

sys.path.append("../technique")

from dotenv import load_dotenv

load_dotenv()
import os

#from compute import compute
from flask import jsonify, Flask, request, redirect, send_file, session
from flask_cors import CORS

application = Flask(__name__, static_folder="front/out", static_url_path="/")
application.secret_key = os.getenv("SECRET_KEY")
CORS(application, origins="*")

client_id = os.getenv("OAUTH_CLIENT_ID")
client_secret = os.getenv("OAUTH_CLIENT_SECRET")
oauth_authorize_url = os.getenv('OAUTH_AUTHORIZE_URL')
oauth_logout_url = os.getenv('OAUTH_LOGOUT_URL')
oauth_token_url = os.getenv('OAUTH_TOKEN_URL')
oauth_userinfo_url = os.getenv('OAUTH_USERINFO_URL')

BASE_URL = os.getenv('BASE_URL')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')

@application.route("/")
def index():
    return application.send_static_file("index.html")


import urllib.parse
@application.route("/login")
def login():
    url = f'{oauth_authorize_url}?'
    params = {
    'client_id': client_id,
    'state': "42",
    "response_type":"code",
    "scope": "openid email profile",
    "redirect_uri": f"{BASE_URL}/auth"
    }

    full_path = url + urllib.parse.urlencode(params)
    return redirect(full_path)


@application.route("/logout")
def logout():
    url = f'{oauth_logout_url}?'
    params = {
    "post_logout_redirect_uri": f'{BASE_URL}/',
    "id_token_hint": session['id_token'] if 'id_token' in session else None
    }

    full_path = url + urllib.parse.urlencode(params)
    if 'email' in session:
        session.pop('email')
    return redirect(full_path)


import requests
@application.route("/auth")
def auth():
    code = request.args.get('code')
    access_token_url = oauth_token_url
    params = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        "redirect_uri": f"{BASE_URL}/auth"
    }
    res_token = requests.post(access_token_url, data=params,
        headers={
        "accept": "application/json"})
    res_token_json = res_token.json()
    token = res_token_json['access_token']
    res_info = requests.get(oauth_userinfo_url, headers={"authorization": f"bearer {token}"})
    session['id_token'] = res_token_json['id_token']
    session['email'] = res_info.json()['email']
    return redirect('/')


@application.route("/me")
def me():
    if 'email' in session:
        return jsonify({'email': session['email']})
    else:
        return jsonify({'error': 'not logged in'})

@application.route("/budget", methods=["POST"])
def budget():
    subject = request.form['subject']
    timestamp = '12'
    login = 'thomas.guillet'

    if 'file' not in request.files:
        return
    f = request.files['file']
    filename = f'{UPLOAD_FOLDER}/{subject}_{timestamp}_{login}.ods'
    f.save(filename)
    return send_file(filename)


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
