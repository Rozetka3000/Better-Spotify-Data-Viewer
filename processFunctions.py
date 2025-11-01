import requests
import json
import base64
from PIL import Image
from io import BytesIO
import apikeys
from datetime import datetime


client_id = apikeys.client_id
client_secret = apikeys.client_secret

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type":"client_credentials"}
    
    result = requests.post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

token = get_token()
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}



def spotify_time_to_normal_time(spotify_time):
    time = datetime.fromisoformat(spotify_time.replace('Z', '+00:00'))
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    return time

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search?"
    headers = get_auth_header(token)
    query = f"q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)
    #print(json_result)

def get_artist(artist_id):
    url = "https://api.spotify.com/v1/artists/"
    headers = get_auth_header(token)
    query_url = url + artist_id
    
    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)

    return json_result

# only to be used before you unfuck the data
def count_plays(song_name, unworked_data, thirty_sec_rule):
    count = 0

    for song in unworked_data:
        if song_name == song["master_metadata_track_name"]:
            if thirty_sec_rule:
                ms_played = song["ms_played"]

                if ms_played >= 30000:
                    count = count + 1
            else:
                count = count + 1

    return count

def image_from_url(url, ctk, size=(640, 640)):
    response = requests.get(url)
    response.raise_for_status()
    
    image = Image.open(BytesIO(response.content))
    
    # Resize
    if size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    
    # Convert to CTkImage
    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
    return ctk_image

def get_song_cover(song_id):
    url = "https://api.spotify.com/v1/tracks/"
    headers = get_auth_header(token)
    query_url = url + song_id

    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)
    
    if "album" in json_result and "images" in json_result["album"] and len(json_result["album"]["images"]) > 0:
        return json_result["album"]["images"][0]["url"]
    else:
        print(f"Fuck spotify. No image found for: {song_id}")
        return None
    

def get_song_display_info(song_id, unfucked_data):
    image_url = get_song_cover(song_id)

    for song in unfucked_data:
        if song["song_id"] == song_id:                
            print(f"Finished {song["song_name"]}!!!!")

            return { 
                "timestamps": song["timestamps"],
                "all_miliseconds": song["all_miliseconds"],
                "average_time_listened": song["average_time_listened"],
                "skips": song["skips"],
                "times_on_shuffle": song["times_on_shuffle"],
                "song_name": song["song_name"],
                "song_id": song["song_id"],
                "artist_name": song["artist_name"],
                "times_played": song["times_played"],
                "registered_times_played": song["registered_times_played"],
                "cover_url": image_url
            }

    return "Kill yourself"