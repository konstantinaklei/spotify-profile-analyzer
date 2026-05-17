import os
from flask import Flask, request, redirect, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/callback"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-top-read"
)

@app.route('/')
def index():
    auth_url = sp_oauth.get_authorize_url()
    return f'''
        <h1>Στατιστικά Spotify</h1>
        <a href="{auth_url}">Σύνδεση με το Spotify λογαριασμό σου</a>
    '''

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    return redirect('/stats')

@app.route('/stats')
def stats():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('/') 

    sp = spotipy.Spotify(auth=token_info['access_token'])

    top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')
    
    html = "<h2>Τα 10 Αγαπημένα σου Τραγούδια:</h2><ul>"
    for track in top_tracks['items']:
        song_name = track['name']
        artist_name = track['artists'][0]['name']
        html += f"<li><b>{song_name}</b> από <i>{artist_name}</i></li>"
    html += "</ul>"

    return html

if __name__ == '__main__':
    app.run(port=5000, debug=True)