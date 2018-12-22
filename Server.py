import base64
import json
import os
import pathlib
import urllib.request
import uuid

import gevent
import requests
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sockets import Sockets
from werkzeug.utils import secure_filename
from Manager import FestifyManager

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
sockets = Sockets(app)

Festify = FestifyManager()

with open('testImg.txt', 'r') as img_file:
    test_img = img_file.readlines()

CLIENT_ID = os.environ['FESTIFY_CLIENT_ID']
CLIENT_SECRET = os.environ['FESTIFY_CLIENT_SECRET']

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/auth".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

app.secret_key = os.environ.get('FLASK_SECRET_KEY', b'$95%89c#5a9fd1')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)

    image = request.files['image']
    if image and allowed_file(image.filename):
        file_type = pathlib.Path(image.filename).suffix
        playlist_id = str(uuid.uuid4())
        image.filename = playlist_id + file_type
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        session['image'] = filename
        session['id'] = playlist_id
        return redirect(url_for('.authorization'))


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}


@app.route("/authorize")
def authorization():
    url_args = "&".join(["{}={}".format(key, urllib.request.quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@sockets.route('/status')
def echo_socket(ws):
    while True:
        status_check = ws.receive()
        status_check = json.loads(status_check)

        results = Festify.get_results(status_check['id'])

        msg = {
            'id': status_check['id'],
            'result': results
        }

        if results:
            ws.send(json.dumps(msg))

        gevent.sleep(10)

@app.route('/festify')
def festify():
    run_id = request.args.get('run_id', None)
    return render_template('status.html', run_id=run_id)


@app.route("/callback/auth")
def authorization_callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode(bytes("{}:{}".format(CLIENT_ID, CLIENT_SECRET), encoding='utf-8')).decode('utf-8')
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]

    image_id = session['image']
    playlist_id = session['id']
    session.clear()
    run_id = Festify.start('Festifys Python', playlist_id, image_id, access_token)

    return redirect(url_for('.festify', run_id=run_id))


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    HOST_IP = '127.0.0.1'
    HOST_PORT = 8080
    HOST_ADDRESS = (HOST_IP, HOST_PORT)

    server = pywsgi.WSGIServer(HOST_ADDRESS, app, handler_class=WebSocketHandler)
    print(f'Serving Festify on http://{HOST_IP}:{HOST_PORT}')
    server.serve_forever()
