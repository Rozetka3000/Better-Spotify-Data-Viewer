import requests
import json
import base64
from PIL import Image, ImageTk
from io import BytesIO
import apikeys


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

def searchForTrack(url):
    if url.startswith('spotify:track:'):
        url = url.replace('spotify:track:', '')

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

def get_song_display_info(song_id, unworked_data, thirty_sec_rule):
    if song_id.startswith('spotify:track:'):
        song_id = song_id.replace('spotify:track:', '')

    url = "https://api.spotify.com/v1/tracks/"
    headers = get_auth_header(token)
    query_url = url + song_id

    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)
    #print(json_result)

    artists = []
    artists_data = json_result["artists"]
    
    for i in range(len(artists_data)):
        artist_name = artists_data[i]["name"]
        artists.append(artist_name)
    
    song_name = json_result["name"]
    times_played = count_plays(song_name, unworked_data, thirty_sec_rule)

    image_url = json_result["album"]["images"][0]["url"]

    print(f"Finished {song_name}!!!!")
    return { 
        "name": song_name,
        "artists": artists,
        "times_played": times_played,
        "cover_url": image_url
    }