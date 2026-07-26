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
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term') #'short_term' = last 4 weeks
        
        # collecting artists
        top_artists = sp.current_user_top_artists(limit=10, time_range='short_term')

        #genres
        all_genres = []
        for artist in top_artists['items']:
            all_genres.extend(artist.get('genres', []))
        genres_text = " ".join(all_genres).lower()

        vibe_scores = {
            'rap': 0,
            'rock': 0,
            'pop': 0,
            'indie': 0
        }

        for genre in all_genres:
            genre_lower = genre.lower()
            if 'rap' in genre_lower or 'hip hop' in genre_lower or 'trap' in genre_lower or 'drill' in genre_lower:
                vibe_scores['rap'] += 1
            elif 'rock' in genre_lower or 'metal' in genre_lower or 'punk' in genre_lower:
                vibe_scores['rock'] += 1
            elif 'pop' in genre_lower or 'dance' in genre_lower or 'house' in genre_lower:
                vibe_scores['pop'] += 1
            elif 'indie' in genre_lower or 'alternative' in genre_lower or 'folk' in genre_lower:
                vibe_scores['indie'] += 1

        dominant = max(vibe_scores, key=vibe_scores.get)
        max_score = vibe_scores[dominant]

        if max_score == 0:
            matched_genre = "Its complicated"
            outfit = "Άνετα, χαλαρά ρούχα, το δικό σου μοναδικό στυλ!"
            hobby = "Road trips, ταινίες και ανακάλυψη νέας μουσικής."
            destination = "Κάπου παραθαλάσσια στην Ελλάδα!"
        elif dominant == 'rap':
            matched_genre = "Rap / Hip-Hop "
            outfit = "Oversized ρούχα, sneakers και γενικά Streetwear καταστάσεις! "
            hobby = "Skateboard, Graffiti ή απλά άραγμα σε πλατείες με την παρέα."
            destination = "Νέα Υόρκη ή Βερολίνο!"
        elif dominant == 'rock':
            matched_genre = "Rock / Metal "
            outfit = "Μαύρα ρούχα, δερμάτινα μπουφάν, αρβύλες και σκουρόχρωμο μακιγιάζ"
            hobby = "Συναυλίες, συλλογή βινυλίων ή εκμάθηση ηλεκτρικής κιθάρας."
            destination = "Λονδίνο ή Άμστερνταμ"
        elif dominant == 'pop':
            matched_genre = "Pop / Dance "
            outfit = "Casual Chic, φωτεινά χρώματα και ό,τι είναι trend! "
            hobby = "Χορός, φωτογραφία ή δημιουργία περιεχομένου."
            destination = "Παρίσι ή Λος Άντζελες!"
        elif dominant == 'indie':
            matched_genre = "Indie / Alternative "
            outfit = "Vintage κομμάτια, thrift shop ευρήματα, tote bags."
            hobby = "Διάβασμα σε cozy καφέ, φωτογραφία με φιλμ, φεστιβάλ."
            destination = "Βαρκελώνη ή Φλωρεντία!"
        return render_template('index.html', 
                               matched_genre = matched_genre,
                               user_name=user_name, 
                               tracks=top_tracks['items'], 
                               artists=top_artists['items'],
                               outfit=outfit,
                               hobby=hobby,
                               destination=destination)

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            session.pop('token_info', None) 
            return redirect('/')
        else:
            return f"Προέκυψε ένα σφάλμα με το Spotify: {e}"

        
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