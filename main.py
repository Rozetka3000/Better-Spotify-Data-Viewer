import customtkinter as ctk
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import processFunctions as pf
import base64
from requests import post
import os
from datetime import datetime
import time
from collections import defaultdict

client_id = pf.client_id
client_secret = pf.client_secret

client_credentials_manager = SpotifyClientCredentials(
    client_id = client_id,
    client_secret = client_secret
)

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type":"client_credentials"}
    
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

token = get_token()

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

app = ctk.CTk()
app.geometry("1280x720")
app.title("Spotify data visualizer")
app._set_appearance_mode("dark")
app.resizable(False, False)

appdata_folder = os.environ.get("APPDATA")
app_name = "Spotifystatsforfree"
app_folder = os.path.join(appdata_folder, app_name)
os.makedirs(app_folder, exist_ok=True)
stitched_data_path = os.path.join(app_folder, "user_listening_data.json")
unfucked_data_path = os.path.join(app_folder, "unfucked_user_data.json")
cached_images_folder = os.path.join(app_folder, "Cached images")
os.makedirs(cached_images_folder, exist_ok=True)

jsonData = None
unworked_data = None
unfucked_data = None

if os.path.exists(stitched_data_path):
    with open(stitched_data_path, 'r', encoding="utf-8") as jsonData:
        unworked_data = json.load(jsonData)
else:
    data_files = ctk.filedialog.askopenfilenames(title="Choose your JSON files that contain your listening data!", filetypes=[("JSON files", "*.json")])

    if data_files:
        file_confirm_window = ctk.CTkToplevel(app)
        file_confirm_window.geometry("330x70")
        file_confirm_window.resizable(False, False)
        file_confirm_window.title("Files selected!")

        error_label = ctk.CTkLabel(file_confirm_window, text=f"You've selected {len(data_files)} JSON files that contain your data!")
        error_label.pack()

        quit_btn = ctk.CTkButton(file_confirm_window, text="Continue", command=lambda: file_confirm_window.destroy())
        quit_btn.pack()

        # stitch the files together
        file_string = ""
        for i in range(len(data_files)):
            if i == 0:
                file_content = open(data_files[i], 'r', encoding="utf-8").read()
                file_content = file_content[:-2]
                file_content = file_content + ","
                file_string = file_string + file_content
            elif i == (len(data_files)-1):
                file_content = open(data_files[i], 'r', encoding="utf-8").read()
                file_content = file_content[1:]
                file_string = file_string + file_content
            else:
                file_content = open(data_files[i], 'r', encoding="utf-8").read()
                file_content = file_content[1:]
                file_content = file_content[:-2]
                file_content = file_content + ","

                file_string = file_string + file_content

        with open(stitched_data_path, 'w', encoding="utf-8") as f:
            f.write(file_string)
    else:
        error_window = ctk.CTkToplevel(app)
        error_window.geometry("500x500")
        error_window.resizable(False, False)
        error_window.title("ERROR, YOU'RE FUCKING STUPID!")

        error_label = ctk.CTkLabel(error_window, text="YOU DIDN'T SELECT ANY FILES, GO FUCK YOURSELF! \n Restart the app and try again!")
        error_label.pack()

        quit_btn = ctk.CTkButton(error_window, text="Quit", command=lambda: quit())
        quit_btn.pack()

def unfuck_the_data():
    global unworked_data

    songs_by_name = defaultdict(lambda: {
        'timestamps': [],
        'all_miliseconds': [],
        'skips': 0,
        'song_id': None,
        'artist_name': None
    })

    for song in unworked_data:
        song_name = song['master_metadata_track_name']
        data = songs_by_name[song_name]
        
        data["timestamps"].append(pf.spotify_time_to_normal_time(song["ts"]))
        data['all_miliseconds'].append(song["ms_played"])

        if song.get("skipped") == True:
            data["skips"] += 1

        if data['song_id'] is None:
            song_id = song.get('spotify_track_uri')

            if song_id is not None:
                data['song_id'] = song_id.replace('spotify:track:', '')
            else:
                data['song_id'] = "unknown"
            
            artist = song.get('master_metadata_album_artist_name')

            if artist is not None:
                data['artist_name'] = artist
            else:
                data["artist_name"] = "Unknown Artist"
        
    
    good_data = []
    i = 1
    for song_name, data in songs_by_name.items():
        times_played = len(data["all_miliseconds"])
        registered_times_played = 0

        for j in range(len(data["all_miliseconds"])):
            if data["all_miliseconds"][j] >= 30000:
                registered_times_played += 1

        song_data = {
            "song_name": song_name,
            "timestamps": data['timestamps'],
            "all_miliseconds": data['all_miliseconds'],
            "average_time_listened": sum(data['all_miliseconds']) / len(data['all_miliseconds']),
            "skips": data['skips'],
            "song_id": data['song_id'],
            "artist_name": data['artist_name'],
            "times_played": times_played,
            "registered_times_played": registered_times_played
        }

        good_data.append(song_data)
        i += 1
        print(song_name)
        print(f"Unfucked the {i}th song")

    json_unfucked_data = json.dumps(good_data)
    with open(unfucked_data_path, 'w', encoding="utf-8") as f:
        f.write(json_unfucked_data)

    return good_data

if os.path.exists(unfucked_data_path):
    with open(unfucked_data_path, 'r', encoding="utf-8") as unfucked_json:
        unfucked_data = json.load(unfucked_json)
else:
    start_time = time.perf_counter()
    unfucked_data = unfuck_the_data()
    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000

    print(f"Unfuck time: {int(elapsed_time_ms)} ms / {int(elapsed_time_ms / 1000)} secs / {elapsed_time_ms / 1000 / 60} min")


# Scroll huita
main_frame = ctk.CTkScrollableFrame(app)
main_frame.pack(fill="both", expand=True)
scroll_bar = ctk.CTkScrollbar(main_frame)

def on_mouse_wheel(event):
    # Multiply the scroll amount for faster scrolling
    main_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120) * 6), "units")

# region Data management top leve
data_management_toplevel = ctk.CTkToplevel(app)
data_management_toplevel.resizable(False, False)
data_management_toplevel.title("Data management")

data_deleting_warning_label = ctk.CTkLabel(data_management_toplevel, text="WARNING: This will also close the program!", text_color="red")
data_deleting_warning_label.grid(row=0, column=0, pady=10, padx=10)

def delete_data(option):
    if option == 0:
        os.remove(unfucked_data_path)

        quit()
    elif option == 1:
        if os.path.exists(unfucked_data_path):
            os.remove(unfucked_data_path)

        os.remove(stitched_data_path)
        quit()

delete_unfucked_data_btn = ctk.CTkButton(data_management_toplevel, text="Delete your processed data", command=lambda: delete_data(0))
delete_unfucked_data_btn.grid(row=1, column=0, pady=10, padx=20)

delete_all_data_btn = ctk.CTkButton(data_management_toplevel, text="Delete ALL your data", command=lambda: delete_data(1))
delete_all_data_btn.grid(row=2, column=0, pady=10, padx=20)
#endregion


# region Settings toplevel
settings_toplevel = ctk.CTkToplevel(app)
settings_toplevel.resizable(False, False)
settings_toplevel.geometry("500x400")
settings_toplevel.title("Configuration")

settings_row = 0
settings_frame = ctk.CTkFrame(settings_toplevel)
settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Centers the damn thing
settings_frame.grid_columnconfigure(0, weight=1)
settings_frame.grid_columnconfigure(1, weight=1)

limit = None
limit_label = ctk.CTkLabel(settings_frame, text="Limit:")
limit_label.grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
limit_field = ctk.CTkEntry(settings_frame)
limit_field.grid(row=settings_row, column=1, padx=(0, 0), pady=10, sticky="w")
limit_field.insert(0, "6")
settings_row += 1

songs_per_row = None
spr_label = ctk.CTkLabel(settings_frame, text="Songs per row:")
spr_label.grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
spr_field = ctk.CTkEntry(settings_frame)
spr_field.grid(row=settings_row, column=1, padx=(0, 0), pady=0, sticky="w")
spr_field.insert(0, "3")
settings_row += 1

thirty_sec_rule = None
shitty_thirty_sec_rule = ctk.StringVar(settings_frame, "on")
tsr_label = ctk.CTkLabel(settings_frame, text="30 second stream rule:")
tsr_label.grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
tsr_checkbox = ctk.CTkCheckBox(settings_frame, text="", variable=shitty_thirty_sec_rule, onvalue="on", offvalue="off")
tsr_checkbox.grid(row=settings_row, column=1, padx=(0, 0), pady=0, sticky="w")
settings_row += 1

# calendar bullshit
def get_earliest_and_last_timestamps(i, t):
    global unfucked_data
    
    songs_to_use = pf.sort_by_date(unfucked_data, False)

    first_and_last = [songs_to_use[0], songs_to_use[-1]]
    timestamp = first_and_last[i][-1]

    date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

    if t == "DD":
        return date.day
    elif t == "MM":
        return date.month
    elif t == "YY":
        return date.year
    elif t == "date":
        return date
    else:
        print("You fucking stupid")

    return timestamp

# start date
start_date = None
start_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
start_frame.grid(row=settings_row, column=0, columnspan=4, pady=5)
ctk.CTkLabel(start_frame, text="Start date: ").grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
start_day = ctk.CTkEntry(start_frame, width=40, placeholder_text="")
start_day.insert(0, get_earliest_and_last_timestamps(0, "DD"))
start_day.grid(row=settings_row, column=1, padx=(0, 5))
start_month = ctk.CTkEntry(start_frame, width=40, placeholder_text=get_earliest_and_last_timestamps(0, "MM"))
start_month.insert(0, get_earliest_and_last_timestamps(0, "MM"))
start_month.grid(row=settings_row, column=2, padx=(0, 5))
start_year = ctk.CTkEntry(start_frame, width=60, placeholder_text=get_earliest_and_last_timestamps(0, "YY"))
start_year.grid(row=settings_row, column=3, padx=(0, 5))
start_year.insert(0, get_earliest_and_last_timestamps(0, "YY"))
settings_row += 1

# end date
end_date = None
end_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
end_frame.grid(row=settings_row, column=0, columnspan=4, pady=5)
ctk.CTkLabel(end_frame, text="End Date:").grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
end_day = ctk.CTkEntry(end_frame, width=40, placeholder_text=get_earliest_and_last_timestamps(1, "DD"))
end_day.grid(row=settings_row, column=1, padx=(0, 5))
end_day.insert(0, get_earliest_and_last_timestamps(1, "DD"))
end_month = ctk.CTkEntry(end_frame, width=40, placeholder_text=get_earliest_and_last_timestamps(1, "MM"))
end_month.grid(row=settings_row, column=2, padx=(0, 5))
end_month.insert(0, get_earliest_and_last_timestamps(1, "MM"))
end_year = ctk.CTkEntry(end_frame, width=60, placeholder_text=get_earliest_and_last_timestamps(1, "YY"))
end_year.grid(row=settings_row, column=3, padx=(0, 5))
end_year.insert(0, get_earliest_and_last_timestamps(1, "YY"))
settings_row += 1

order_label = ctk.CTkLabel(settings_frame, text="Displaying of data:")
order_label.grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
order_dropdown = ctk.CTkComboBox(settings_frame, 
                                 values=["Chronologicaly", 
                                        "Chronologicaly descending",
                                        "Your most streamed",
                                        "Your least streamed",
                                        "Average time listened (by %)",
                                        "Skips",
                                        "Minutes listened since X",
                                        "Search song",
                                        "Top artists"
                                        ])
order_dropdown.set("Your most streamed")
order_dropdown.grid(row=settings_row, column=1, padx=(0, 0), pady=0, sticky="w")
settings_row += 1


def set_bs():
    global limit, songs_per_row, thirty_sec_rule, start_date, end_date
    limit = int(limit_field.get())
    songs_per_row = int(spr_field.get())
    
    start_day_val = start_day.get()
    start_month_val = start_month.get()
    start_year_val = start_year.get()

    end_day_val = end_day.get()
    end_month_val = end_month.get()
    end_year_val = end_year.get()

    start_date = datetime(year=int(start_year_val), month=int(start_month_val), day=int(start_day_val))
    end_date = datetime(year=int(end_year_val), month=int(end_month_val), day=int(end_day_val))
    
    for widget in main_frame.winfo_children():
        widget.destroy()

    for i in range(songs_per_row):
        main_frame.grid_columnconfigure(i, weight=1)

    placeholder_thirty_sec_rule = shitty_thirty_sec_rule.get()
    
    if placeholder_thirty_sec_rule == "on":
        thirty_sec_rule = True
    else:
        thirty_sec_rule = False

    initialize_song_page()

config_btn = ctk.CTkButton(
    settings_frame,
    text="Config",
    command=lambda: set_bs()
)
config_btn.grid(row=settings_row, column=0, columnspan=2, pady=20, sticky="s")
settings_row += 1
# endregion

def sorted_songs(crescator):
    songs={}

    index = 0
    for song in unworked_data:
        song_id = song['spotify_track_uri']

        if song_id.startswith('spotify:track:'):
            song_id = song_id.replace('spotify:track:', '')

        song_name = song["master_metadata_track_name"]
        plays = pf.count_plays(song_name, unworked_data, thirty_sec_rule)
        
        songs[song_id] = plays
        
        index += 1
        #print(index)

    return sorted(songs.items(), key=lambda x: x[1], reverse=crescator)

def back_to_normal_page():
    for widget in main_frame.winfo_children():
        widget.destroy()

    set_bs()

def go_to_song_page(song_data):
    for widget in main_frame.winfo_children():
        widget.destroy()

    center_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    center_frame.pack(expand=True, fill="both", padx=50, pady=50)

    center_frame.grid_columnconfigure(0, weight=1)
    center_frame.grid_columnconfigure(1, weight=2)
    center_frame.grid_rowconfigure(0, weight=1)

    # Song cover
    left_frame = ctk.CTkFrame(center_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

    song_image = pf.handle_cover_bullshit(song_data["song_id"], ctk, size=(400, 400))
    song_image_label = ctk.CTkLabel(left_frame, image=song_image, text="")
    song_image_label.pack(expand=True, padx=20, pady=20)

    # Info and bs
    info_frame = ctk.CTkFrame(center_frame)
    info_frame.grid(row=0, column=1, sticky="nsew")

    # Header (idi nahui)
    header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=20)

    song_title = song_data["song_name"]
    song_artist = song_data["artist_name"]
    title_label = ctk.CTkLabel(header_frame, text=f'{song_title} \nby {song_artist}', font=("Arial", 40, "bold"), justify="left")
    title_label.pack(anchor="w")
    
    skips = song_data["skips"]
    times_played = song_data["times_played"]
    total_mins = sum(song_data["all_miliseconds"]) / 1000 / 60
    registered_times_played = song_data["registered_times_played"]
    average_time_listened = round(song_data['average_time_listened'] / 1000 / 60)

    song_info_text = f"Times played (<30s): {times_played} \nTimes played (=>30s): {registered_times_played} \nTimes skiped: {skips} \nAverage time listened: {average_time_listened} minutes \nFirst time listened: {pf.make_date_prettier(song_data["timestamps"][0])} \nLast time listened: {pf.make_date_prettier(song_data["timestamps"][-1])} \nTotal minutes listened: {int(total_mins)}"
    song_info_text = song_info_text[:-1]
    song_info = ctk.CTkLabel(info_frame, text=song_info_text, font=("Arial", 25), justify="left")
    song_info.pack(padx=23, pady=10, anchor="w")

    back_btn = ctk.CTkButton(main_frame, text="Back", font=("Arial", 20), command=lambda: back_to_normal_page())
    back_btn.pack(side="bottom", anchor="se", padx=20, pady=130)
    
def go_to_artist_page(artist_name, artist_data):
    for widget in main_frame.winfo_children():
        widget.destroy()

    center_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    center_frame.pack(expand=True, fill="both", padx=50, pady=50)

    center_frame.grid_columnconfigure(0, weight=1)
    center_frame.grid_columnconfigure(1, weight=2)
    center_frame.grid_rowconfigure(0, weight=1)

    # Artist image
    left_frame = ctk.CTkFrame(center_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

    artist_image = pf.handle_artist_image_bullshit(artist_name, ctk, size=(400, 400))
    artist_image_label = ctk.CTkLabel(left_frame, image=artist_image, text="")
    artist_image_label.pack(expand=True, padx=20, pady=20)

    # Info and bs
    info_frame = ctk.CTkFrame(center_frame)
    info_frame.grid(row=0, column=1, sticky="nsew")

    # Header (idi nahui)
    header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=20)

    title_label = ctk.CTkLabel(header_frame, text=artist_image, font=("Arial", 40, "bold"), justify="left")
    title_label.pack(anchor="w")
    
    _times_played = artist_data["times_played"]
    total_mins = artist_data["total_ms"] / 60000
    registered_times_played = artist_data["registered_times_played"]

    times_played = 0
    if thirty_sec_rule:
        times_played = _times_played
    else:
        times_played = registered_times_played

    artist_info_text = f"Times listened: {times_played} \nTotal minutes: {total_mins}"
    artist_info = ctk.CTkLabel(info_frame, text=artist_info_text, font=("Arial", 25), justify="left")
    artist_info.pack(padx=23, pady=10, anchor="w")

    back_btn = ctk.CTkButton(main_frame, text="Back", font=("Arial", 20), command=lambda: back_to_normal_page())
    back_btn.pack(side="bottom", anchor="se", padx=20, pady=130)

def process_artist(artist_name, artist_data, row, col):
    artist_frame = ctk.CTkFrame(main_frame)
    artist_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    total_listens = 0
    if thirty_sec_rule:
        total_listens = artist_data["registered_times_played"]
    else:
        total_listens = artist_data["times_played"]

    mins_listened = artist_data["total_ms"] / 1000 / 60

    artist_info = f"Artist name: {artist_name} \nTimes played: {total_listens} \nTime listened: {int(mins_listened)} mins / {int(mins_listened / 60)} hours"

    artist_label = ctk.CTkLabel(artist_frame, text=artist_info, font=("Arial", 14))
    artist_image = pf.handle_artist_image_bullshit(artist_name, ctk, size=(200, 200))
    artist_image_btn = ctk.CTkButton(artist_frame, image=artist_image, text="", command=lambda: go_to_artist_page(artist_name, artist_data), fg_color="black", hover_color="white")

    artist_label.pack(pady=10)
    artist_image_btn.pack(pady=10)

def process_song(song_data, row, col, data_to_show):
    song_frame = ctk.CTkFrame(main_frame)
    song_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    song_info = f"Song name: {song_data['song_name']}\nArtist: {song_data['artist_name']}\n"

    
    for field in data_to_show:
        text, val = field

        if field == "first/last timestamp":
                if order_dropdown.get() == "Chronologicaly":
                    song_info = song_info + "Listened on" + ": " + str(pf.make_date_prettier(song_data["timestamps"][0])) + "\n"
                else:
                    song_info = song_info + "Listened on" + ": " + str(pf.make_date_prettier(song_data["timestamps"][-1])) + "\n"
        else:
            song_info = song_info + text + str(val) + "\n"

    if song_info[-1] == "\n":
        song_info = song_info[:-1]
    
    song_label = ctk.CTkLabel(song_frame, text=song_info, font=("Arial", 14))
    song_image = pf.handle_cover_bullshit(song_data["song_id"], ctk, size=(200, 200))
    song_image_btn = ctk.CTkButton(song_frame, image=song_image, text="", command=lambda: go_to_song_page(song_data), fg_color="black", hover_color="white")

    song_label.pack(pady=10)
    song_image_btn.pack(pady=10)

# have skips be updated too when according for time
def initialize_song_page():
    songs_analized = []
    songs_to_use = []

    # recalc unfucked_data using timestamps
    _unfucked_data = None
    _unfucked_data = unfucked_data.copy()
    for_removing = []
    for song in _unfucked_data:
        timestamps = song["timestamps"]
        all_miliseconds = song["all_miliseconds"]

        filtered_timestamps = []
        filtered_ms = []

        for i, timestamp in enumerate(timestamps):
            _timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

            if start_date <= _timestamp <= end_date:
                filtered_timestamps.append(timestamp)
                filtered_ms.append(all_miliseconds[i])

        if len(timestamps) == 0:
            for_removing.append(song)
            continue

        song["timestamps"] = filtered_timestamps
        song["all_miliseconds"] = filtered_ms

        # recalc all_milisecond, avg time listened, number of plays...
        average_time_listened = 0
        if len(filtered_ms) != 0:
            average_time_listened = sum(filtered_ms) / len(filtered_ms)
        
        times_played = 0
        registered_times_played = len(filtered_timestamps)
        
        for ms in filtered_ms:
            if ms > 30000:
                times_played += 1

        song["average_time_listened"] = average_time_listened
        song["times_played"] = times_played
        song["registered_times_played"] = registered_times_played

    for song in for_removing:
        _unfucked_data.remove(song)
      
    row = 0
    col = 0

    if order_dropdown.get() == "Your most streamed" or order_dropdown.get() == 'Your least streamed':
        if thirty_sec_rule:
            if order_dropdown.get() == 'Your most streamed':
                songs_to_use = pf.sort_songs_by("registered_times_played", _unfucked_data, True)
            else:
                songs_to_use = pf.sort_songs_by("registered_times_played", _unfucked_data, False)
        else:
            if order_dropdown.get() == 'Your most streamed':
                songs_to_use = pf.sort_songs_by("times_played", _unfucked_data, True)
            else:
                songs_to_use = pf.sort_songs_by("times_played", _unfucked_data, False)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, _unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                if thirty_sec_rule:
                    process_song(song_data, row, col, [("Times played: ", song_data["registered_times_played"]), ("Total hours: ", int(sum(song_data["all_miliseconds"])/1000/60/60))])
                    print(sum(song_data["all_miliseconds"]))
                else:
                    process_song(song_data, row, col, [("Times played: ", song_data["times_played"]), ("Total hours: ", int(sum(song_data["all_miliseconds"])/1000/60/60))])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Average time listened (by %)":
        _songs_to_use = pf.sort_songs_by("average_time_listened", _unfucked_data, True)

        # from ms to %
        for i in range(len(_songs_to_use)):
            if i == limit:
                break

            song = _songs_to_use[i]

            song_length = pf.get_song_length(song[0])
            avg_ms = song[1]
            perc = int((avg_ms / song_length) * 100)
            
            songs_to_use.append([song[0], perc])

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, _unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                if thirty_sec_rule:
                    process_song(song_data, row, col, [("Times played: ", song_data["registered_times_played"])])
                else:
                    process_song(song_data, row, col, [("Times played: ", song_data["times_played"])])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Skips":
        songs_to_use = pf.sort_songs_by("skips", _unfucked_data, True)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, _unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, [("Skips: ", song_data["skips"])])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Chronologicaly" or order_dropdown.get() == "Chronologicaly descending":
        reverse = False
        if order_dropdown.get() == "Chronologicaly descending":
            reverse = True
        
        songs_to_use = pf.sort_by_date(_unfucked_data, reverse)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, _unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, [("first/last timestamp", 0)])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Minutes listened since X":
        songs_to_use = _unfucked_data
        total_ms = 0

        for song in _unfucked_data:
            total_ms += sum(song["all_miliseconds"])

        total_mins = total_ms / 1000 / 60
        total_hours = total_mins / 60

        total_songs = len(_unfucked_data)

        song_label = ctk.CTkLabel(main_frame, text=f"From {start_date} until {end_date}, you've listened to:\n {int(total_mins)} minutes, aka {int(total_hours)} hours \n In those dates you listened to {total_songs} songs", font=("Arial", 30))
        song_label.pack(pady=10)
    elif order_dropdown.get() == "Search song":
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=0)

        search_song_label = ctk.CTkLabel(main_frame, text="Search a song:", font=("Arial", 30))
        search_song_field = ctk.CTkEntry(main_frame, placeholder_text="Song name...", font=("Arial", 20))

        search_song_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")
        search_song_field.grid(row=0, column=1, padx=(0, 10), pady=20, sticky="ew")
        
        def handle_search():
            result = pf.search_for_song(search_song_field.get(), _unfucked_data)

            if result is not None:
                song_data = pf.get_song_display_info(result["song_id"], _unfucked_data)

                process_song(song_data, 1, 0, [])

                main_frame.update()
        
        search_song_btn = ctk.CTkButton(main_frame, text="Search for the song", command=lambda: handle_search(), font=("Arial", 20))
        search_song_btn.grid(row=0, column=1, sticky="e")
    elif order_dropdown.get() == "Top artists":
        reverse = True

        topartists_level_toplevel = ctk.CTkToplevel(app)
        topartists_level_toplevel.resizable(False, False)
        topartists_level_toplevel.title("Top artist search settings")
        #topartists_level_toplevel.geometry("300x200")

        artist_sorting_label = ctk.CTkLabel(topartists_level_toplevel, text="Artist sorting method:")
        artist_sorting_label.grid(row=0, column=0, padx=10, pady=10)
        
        artist_sorting_method = ctk.CTkComboBox(topartists_level_toplevel, values=["Sort by number of plays (Wrapped method)", "Sort by total time listened"])
        artist_sorting_method.grid(row=1, column=0, padx=10, pady=10)

        def process_top_artists(_unfucked_data, row, col):
            artists = {}
            for song in _unfucked_data:
                artist = song["artist_name"]
                registered_times_played = song["registered_times_played"]
                times_played = song["times_played"]
                total_ms = sum(song["all_miliseconds"])

                if artist in artists:
                    artists[artist]["registered_times_played"] += registered_times_played
                    artists[artist]["times_played"] += times_played
                    artists[artist]["total_ms"] += total_ms
                else:
                    artists[artist] = {
                        "registered_times_played": registered_times_played,
                        "times_played": times_played,
                        "total_ms": total_ms
                    }

            sorted_artists = None
            if artist_sorting_method.get() == "Sort by number of plays (Wrapped method)":
                if thirty_sec_rule:
                    sorted_artists = sorted(artists.items(), key=lambda x: x[1]['registered_times_played'], reverse=reverse)
                else:
                    sorted_artists = sorted(artists.items(), key=lambda x: x[1]['times_played'], reverse=reverse)
            elif artist_sorting_method.get() == "Sort by total time listened":
                sorted_artists = sorted(artists.items(), key=lambda x: x[1]['total_ms'], reverse=reverse)

            index = 0
            for key, val in sorted_artists:
                if index < limit:
                    process_artist(key, val, row=row, col=col)

                    col += 1
                    if col >= songs_per_row:
                        col = 0
                        row += 1

                    main_frame.update()
                    index += 1

        go_btn = ctk.CTkButton(topartists_level_toplevel, command=lambda: process_top_artists(_unfucked_data, row, col), text="Go!")
        go_btn.grid(row=2, column=0, padx=10, pady=10)




app.mainloop()