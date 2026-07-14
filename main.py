import os
from flask import Flask, request, redirect, session, render_template
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

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        # collecting user's info
        user_profile = sp.current_user()
        user_name = user_profile.get('display_name')

        # collecting songs
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')
        
        # collecting artists
        top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
        
        return render_template('index.html', 
                               user_name=user_name, 
                               tracks=top_tracks['items'], 
                               artists=top_artists['items'])
       
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            session.pop('token_info', None) # delete the expired token
            return redirect('/')
        else:
            return f"Προέκυψε ένα σφάλμα με το Spotify: {e}"

if __name__ == '__main__':
    app.run(port=5000, debug=True)