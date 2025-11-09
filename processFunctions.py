import requests
import json
import base64
from PIL import Image
from io import BytesIO
import apikeys
from datetime import datetime
import ast
import os

client_id = apikeys.client_id
client_secret = apikeys.client_secret

appdata_folder = os.environ.get("APPDATA")
app_name = "Spotifystatsforfree"
app_folder = os.path.join(appdata_folder, app_name)
os.makedirs(app_folder, exist_ok=True)
stitched_data_path = os.path.join(app_folder, "user_listening_data.json")
unfucked_data_path = os.path.join(app_folder, "unfucked_user_data.json")
cached_images_folder = os.path.join(app_folder, "Cached images")
os.makedirs(cached_images_folder, exist_ok=True)


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

    return 

def get_artist_id(artist_name):
    url = "https://api.spotify.com/v1/search/"
    headers = get_auth_header(token)
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 1
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data["artists"]["items"]:
        artist = data["artists"]["items"][0]
        return artist["id"]
    else:
        return None

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

def sort_by_date(unfucked_data, reverse):
    only_timestamps = []

    for song in unfucked_data:
        song_id = song["song_id"]
        timestamps = song["timestamps"]

        for timestamp in timestamps:
            only_timestamps.append((song_id, timestamp))
            
    songs_to_use = sorted(only_timestamps, key=lambda x: x[1], reverse=reverse)
    return songs_to_use


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

def handle_cover_bullshit(song_id, ctk, size=(640, 640)):
    cached_image_path = os.path.join(cached_images_folder, f"{song_id}.jpg")

    if os.path.exists(cached_image_path):
        #image_content = open(cached_image_path, 'rb').read()
        image = Image.open(cached_image_path)
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
        return ctk_image
    else:
        image_url = get_song_cover(song_id)
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)

        with open(cached_image_path, 'wb') as f:
            image.save(f, "JPEG")
            
        return ctk_image

def handle_artist_image_bullshit(artist_name, ctk, size=(640, 640)):
    cached_image_path = os.path.join(cached_images_folder, f"{artist_name}.jpg")
    if os.path.exists(cached_image_path):
        image = Image.open(cached_image_path)
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
        return ctk_image
    else:
        artist_id = get_artist_id(artist_name)
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = get_auth_header(token)
        response = requests.get(url, headers=headers)
        data = response.json()
        
        artist_img_url = data["images"][0]["url"]

        response = requests.get(artist_img_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        ctk_image = None
        if image:
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)

        with open(cached_image_path, 'wb') as f:
            image.save(f, "JPEG")
            
        return ctk_image



def get_song_length(song_id):
    url = f"https://api.spotify.com/v1/tracks/{song_id}"
    headers = get_auth_header(token)
    
    result = requests.get(url, headers=headers)
    json_result = json.loads(result.content)
    
    duration_ms = json_result["duration_ms"]
    return duration_ms

# can only be used on bullshit that aren't arrays
def sort_songs_by(parameter, unfucked_data, crescator):
    data = {}

    for song in unfucked_data:
        data[song["song_id"]] = song[parameter]

    #print(sorted(data.items(), key=lambda x: x[1], reverse=crescator))
    return sorted(data.items(), key=lambda x: x[1], reverse=crescator)

def make_date_prettier(date):
    _date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    format = "%B %d, %Y at %I:%M %p"

    return _date.strftime(format)

def search_for_song(song_to_search, data):
    for song in data:
        if type(song["song_name"]) == str:
            if song["song_name"].lower() == song_to_search.lower():
                #print(song)
                return song

def get_song_display_info(song_id, unfucked_data):
    #image_url = get_song_cover(song_id)

    for song in unfucked_data:
        if song["song_id"] == song_id:                
            print(f"Finished {song["song_name"]}!!!!")

            return { 
                "timestamps": song["timestamps"],
                "all_miliseconds": song["all_miliseconds"],
                "average_time_listened": song["average_time_listened"],
                "skips": song["skips"],
                "song_name": song["song_name"],
                "song_id": song["song_id"],
                "artist_name": song["artist_name"],
                "times_played": song["times_played"],
                "registered_times_played": song["registered_times_played"],
                #"cover_url": image_url
            }

    return "Kill yourself"