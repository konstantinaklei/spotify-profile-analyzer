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
        
        artist_ids = []
        for artist in all_artists:
            if artist.get('id') and artist.get('id') not in artist_ids:
                artist_ids.append(artist.get('id'))

        all_genres = []
        
        if artist_ids:
            try:
                full_artists = sp.artists(artist_ids[:50]) 
                for artist in full_artists['artists']:
                    if artist and 'genres' in artist:
                        all_genres.extend(artist['genres'])
            except Exception as e:
                print(f"Σφάλμα κατά την άντληση των πλήρων καλλιτεχνών: {e}")

        if not all_genres:
            print("\nΠΡΟΣΟΧΗ: Δεν βρέθηκε κανένα απολύτως genre στο Spotify σου!")
            dominant = "unknown"
        else:
            genre_counts = Counter(all_genres)
            top_5_genres = genre_counts.most_common(5)
            
            print("\n--- ΤΑ 5 ΚΟΡΥΦΑΙΑ ΕΙΔΗ ΣΟΥ ---")
            for rank, (genre, count) in enumerate(top_5_genres, 1):
                print(f"{rank}. {genre} ({count} εμφανίσεις)")
                
            dominant = top_5_genres[0][0]

        if dominant == "unknown":
            matched_genre = "Its complicated"
            outfit = "Άνετα, χαλαρά ρούχα, το δικό σου μοναδικό στυλ!"
            hobby = "Road trips, ταινίες και ανακάλυψη νέας μουσικής."
            destination = "Κάπου παραθαλάσσια στην Ελλάδα!"
        elif 'rap' in dominant or 'hip hop' in dominant or 'trap' in dominant:
            matched_genre = "Rap / Hip-Hop "
            outfit = "Oversized ρούχα, sneakers και γενικά Streetwear καταστάσεις! "
            hobby = "Skateboard, Graffiti ή απλά άραγμα σε πλατείες με την παρέα."
            destination = "Νέα Υόρκη ή Βερολίνο!"
        elif 'rock' in dominant or 'metal' in dominant:
            matched_genre = "Rock / Metal "
            outfit = "Μαύρα ρούχα, δερμάτινα μπουφάν, αρβύλες και σκουρόχρωμο μακιγιάζ"
            hobby = "Συναυλίες, συλλογή βινυλίων ή εκμάθηση ηλεκτρικής κιθάρας."
            destination = "Λονδίνο ή Άμστερνταμ"
        elif 'pop' in dominant or 'dance' in dominant:
            matched_genre = "Pop / Dance "
            outfit = "Casual Chic, φωτεινά χρώματα και ό,τι είναι trend! "
            hobby = "Χορός, φωτογραφία ή δημιουργία περιεχομένου."
            destination = "Παρίσι ή Λος Άντζελες!"
        elif 'indie' in dominant or 'alternative' in dominant:
            matched_genre = "Indie / Alternative "
            outfit = "Vintage κομμάτια, thrift shop ευρήματα, tote bags."
            hobby = "Διάβασμα σε cozy καφέ, φωτογραφία με φιλμ, φεστιβάλ."
            destination = "Βαρκελώνη ή Φλωρεντία!"
        else:
            matched_genre = dominant.capitalize()
            outfit = "Το δικό σου ξεχωριστό στυλ!"
            hobby = "Να ακούς τη μουσική σου!"
            destination = "Οπουδήποτε!"

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