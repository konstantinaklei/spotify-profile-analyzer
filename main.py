import os
from flask import Flask, request, redirect, session, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import requests
from collections import Counter

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
    scope="user-top-read",
    show_dialog=True,
    cache_handler=spotipy.cache_handler.MemoryCacheHandler()
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/stats')
def stats():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('/') 

    try:
        
        
        if isinstance(token_info, dict):
            access_token = token_info.get('access_token')
        else:
            access_token = token_info

        sp = spotipy.Spotify(auth=access_token)
        user_profile = sp.current_user()
        user_name = user_profile.get('display_name')
        
        top_tracks1 = sp.current_user_top_tracks(limit=10, time_range='short_term') 
        top_tracks2 = sp.current_user_top_tracks(limit=10, time_range='long_term')
        top_artists1 = sp.current_user_top_artists(limit=10, time_range='short_term')
        top_artists2 = sp.current_user_top_artists(limit=10, time_range='long_term')
        all_artists = top_artists1.get('items', []) + top_artists2.get('items', [])
        
        track_ids = [track['id'] for track in top_tracks1['items']]
        
        audio_features = sp.audio_features(track_ids)
        
        total_energy = 0
        total_valence = 0
        valid_tracks = 0
        
        for feature in audio_features:
            if feature:
                total_energy += feature['energy']
                total_valence += feature['valence']
                valid_tracks += 1
                
        avg_energy = total_energy / valid_tracks if valid_tracks > 0 else 0
        avg_valence = total_valence / valid_tracks if valid_tracks > 0 else 0
        
        print(f"\n--- VIBE CHECK ---")
        print(f"Ενέργεια: {avg_energy:.2f} | Διάθεση: {avg_valence:.2f}")

        if avg_energy > 0.7 and avg_valence > 0.6:
            matched_genre = "Party animal"
            outfit = "Φωτεινά χρώματα, εντυπωσιακά sneakers, clubbing & party lifestyle!"
            hobby = "Χορός, γυμναστική."
            destination = "Μύκονος ή Ίμπιζα!"
            
        elif avg_energy > 0.7 and avg_valence <= 0.6:
            matched_genre = "Dark & Intense Vibe"
            outfit = "Μαύρα ρούχα, oversized t-shirts, αρβύλες ή streetwear."
            hobby = "Συναυλίες, skateboard, gaming."
            destination = "Βερολίνο ή Λονδίνο!"
            
        elif avg_energy <= 0.7 and avg_valence > 0.5:
            matched_genre = "Chill & Groovy"
            outfit = "Vintage ρούχα, tote bags, γήινα χρώματα."
            hobby = "Καφές με φίλους, φωτογραφία, road trips."
            destination = "Φλωρεντία ή Βαρκελώνη!"
            
        else:
            matched_genre = "Deep & Melancholic"
            outfit = "Άνετα ρούχα, φούτερ, cozy στυλ."
            hobby = "Διάβασμα βιβλίων, ταινίες στο σπίτι, ποίηση."
            destination = "Ισλανδία ή κάποιο ορεινό χωριό!"

        return render_template('index.html', 
                               matched_genre=matched_genre,
                               user_name=user_name, 
                               tracks1=top_tracks1['items'], 
                               artists1=top_artists1['items'],
                               tracks2=top_tracks2['items'], 
                               artists2=top_artists2['items'],
                               outfit=outfit,
                               hobby=hobby,
                               destination=destination)

    except Exception as e:
        return f"Προέκυψε ένα σφάλμα: {e}"

if __name__ == '__main__':
    app.run(port=5000, debug=True)