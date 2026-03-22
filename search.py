from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from ytmusicapi import YTMusic

# Initialize Server
app = Flask(__name__)
CORS(app) # This allows your React app to talk to Python safely

# Connect to Firebase
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize YouTube Music
ytmusic = YTMusic()

# --- THE WAKE-UP ALARM (This was missing!) ---
@app.route('/ping', methods=['GET'])
def keep_awake():
    # This just replies to UptimeRobot so the server stays awake.
    # It does NOT search YouTube or touch your database!
    return jsonify({"status": "I am awake and ready!"}), 200

# --- YOUR EXISTING SEARCH ENGINE ---
@app.route('/search', methods=['GET'])
def search_and_add():
    # Grab the song name your React app sent
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    print(f"React app requested: {query}. Hunting it down...")

    try:
        # Grab the top 5 closest matches from YouTube
        results = ytmusic.search(query, filter="songs", limit=5)
        new_songs = []

        for track in results:
            video_id = track.get("videoId")
            if not video_id: continue

            title = track.get("title", "Unknown")
            artists_data = track.get("artists", [])
            artist_list = [a.get("name") for a in artists_data] if artists_data else ["Unknown Artist"]
            album_data = track.get("album")
            album_name = album_data.get("name") if album_data else "Single"

            thumbnails = track.get("thumbnails", [])
            cover_url = thumbnails[-1].get("url") if thumbnails else "https://via.placeholder.com/600"
            if "=" in cover_url and "yt3.ggpht" not in cover_url:
                cover_url = cover_url.split("=")[0] + "=w600-h600-l90-rj"

            song_data = {
                "id": video_id,               
                "title": title,
                "artist": artist_list, 
                "genre": "Global Search", # Tag for dynamic additions
                "album": album_name,
                "cover": cover_url,
                "audio": video_id  
            }

            # Save to Firebase instantly
            db.collection("songs").document(video_id).set(song_data, merge=True)
            new_songs.append(song_data)

        # Send the fresh songs straight back to React!
        return jsonify(new_songs)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Runs the API on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
