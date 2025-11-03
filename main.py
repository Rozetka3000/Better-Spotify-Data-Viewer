import customtkinter as ctk
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import processFunctions as pf
import base64
from requests import post
import os
from datetime import datetime

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

jsonData = None
unworked_data = None
unfucked_data = None

if os.path.exists(stitched_data_path):
    jsonData = open(stitched_data_path, 'r', encoding="utf-8")
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
    already_checked = []
    good_data = []

    i = 1
    for song in unworked_data:
        song_name = song['master_metadata_track_name']
        
        if song_name in already_checked:
            continue

        already_checked.append(song_name)

        song_data = {}
        skips = 0
        timestamps = []
        all_miliseconds = []
        for this_song in unworked_data:
            if this_song["master_metadata_track_name"] == song_name:
                timestamps.append(pf.spotify_time_to_normal_time(this_song["ts"]))
                all_miliseconds.append(this_song["ms_played"])

                if this_song["skipped"] == True:
                    skips += 1
        
        average_ms = sum(all_miliseconds) / len(all_miliseconds)

        song_data["timestamps"] = timestamps
        song_data["all_miliseconds"] = all_miliseconds
        song_data["average_time_listened"] = average_ms

        song_data["skips"] = skips

        song_data["song_name"] = song_name

        song_id = song['spotify_track_uri'].replace('spotify:track:', '')
        song_data["song_id"] = song_id

        artist = song['master_metadata_album_artist_name']
        song_data["artist_name"] = artist
        
        unchecked_times_played = pf.count_plays(song["master_metadata_track_name"], unworked_data, False)
        checked_times_played = pf.count_plays(song["master_metadata_track_name"], unworked_data, True)
        song_data["times_played"] = unchecked_times_played
        song_data["registered_times_played"] = checked_times_played

        #song_cover = pf.get_song_cover(song_id)
        #song_data["cover"] = song_cover
        
        good_data.append(song_data)
        
        i += 1
        print(f"Unfucked the {i}th song")

    json_unfucked_data = json.dumps(good_data)
    with open(unfucked_data_path, 'w', encoding="utf-8") as f:
        f.write(json_unfucked_data)

    return good_data

if os.path.exists(unfucked_data_path):
    unfucked_json = open(unfucked_data_path, 'r', encoding="utf-8")
    unfucked_data = json.load(unfucked_json)
else:
    unfucked_data = unfuck_the_data()


# Scroll huita
main_frame = ctk.CTkScrollableFrame(app)
main_frame.pack(fill="both", expand=True)
scroll_bar = ctk.CTkScrollbar(main_frame)

def on_mouse_wheel(event):
    # Multiply the scroll amount for faster scrolling
    main_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120) * 6), "units")

current_page = 0

settings_toplevel = ctk.CTkToplevel(app)
settings_toplevel.resizable(False, False)
settings_toplevel.geometry("500x300")
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
limit_field.insert(0, "5")
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

order_label = ctk.CTkLabel(settings_frame, text="Order of songs:")
order_label.grid(row=settings_row, column=0, padx=(0, 10), pady=10, sticky="e")
order_dropdown = ctk.CTkComboBox(settings_frame, values=["Chronologicaly", "Chronologicaly descending", "Your most streamed", "Your least streamed", "Average time listened (by %)", "Skips"])
order_dropdown.set("Your most streamed")
order_dropdown.grid(row=settings_row, column=1, padx=(0, 0), pady=0, sticky="w")
settings_row += 1

def set_bs():
    global limit, songs_per_row, thirty_sec_rule
    limit = int(limit_field.get())
    songs_per_row = int(spr_field.get())
    
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
        print(index)

    return sorted(songs.items(), key=lambda x: x[1], reverse=crescator)

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

    song_image = pf.image_from_url(song_data["cover_url"], ctk, size=(400, 400))
    song_image_label = ctk.CTkLabel(left_frame, image=song_image, text="")
    song_image_label.pack(expand=True, padx=20, pady=20)

    # Info and bs
    info_frame = ctk.CTkFrame(center_frame)
    info_frame.grid(row=0, column=1, sticky="nsew")

    # Header (idi nahui)
    header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=20)

    song_title = song_data["song_name"]
    title_label = ctk.CTkLabel(header_frame, text=song_title, font=("Arial", 30, "bold"), justify="left")
    title_label.pack(anchor="w")
    
    song_artist = song_data["artist_name"]
    skips = song_data["skips"]
    times_played = song_data["times_played"]
    registered_times_played = song_data["registered_times_played"]
    average_time_listened = song_data['average_time_listened'] / 1000

    song_info_text = f"Artist: {song_artist} \nTimes played (<30s): {times_played} \nTimes played (=>30s): {registered_times_played} \nTimes skiped: {skips} \nAverage time listened: {average_time_listened} \nFirst time listened: {pf.make_date_prettier(song_data["timestamps"][0])} \nLast time listened: {pf.make_date_prettier(song_data["timestamps"][-1])} \n"

    
    song_info_text = song_info_text[:-1]
    
    song_info = ctk.CTkLabel(info_frame, text=song_info_text, font=("Arial", 30), justify="left")

    song_info.pack()
    

def process_song(song_data, row, col, data_to_show):
    song_frame = ctk.CTkFrame(main_frame)
    song_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    song_info = f"Song name: {song_data['song_name']}\nArtist: {song_data['artist_name']}\n"

    times_played = song_data["times_played"]
    if thirty_sec_rule:
        times_played = song_data["registered_times_played"]

    song_info = song_info + f"Times played: {times_played} \n"
    
    for i in range(len(data_to_show)):
        field = data_to_show[i]
        
        if field != "times_played" and field != "registered_times_played":
            if field == "first/last timestamp":
                if order_dropdown.get() == "Chronologicaly":
                    song_info = song_info + "Listened on" + ": " + str(pf.make_date_prettier(song_data["timestamps"][0])) + "\n"
                else:
                    song_info = song_info + "Listened on" + ": " + str(pf.make_date_prettier(song_data["timestamps"][-1])) + "\n"
            else:
                song_info = song_info + field + ": " + str(song_data[field]) + "\n"

    if song_info[-1] == "\n":
        song_info = song_info[:-1]
    
    song_label = ctk.CTkLabel(song_frame, text=song_info, font=("Arial", 14))
    song_image = pf.image_from_url(song_data["cover_url"], ctk, size=(200, 200))
    song_image_btn = ctk.CTkButton(song_frame, image=song_image, text="", command=lambda: go_to_song_page(song_data), fg_color="black", hover_color="white")

    song_image_btn.pack(pady=10)
    song_label.pack(pady=10)

# TO DO: Optimize by makign images be processed later
def initialize_song_page():
    songs_analized = []
    songs_to_use = []
    
    row = 0
    col = 0

    if order_dropdown.get() == "Your most streamed" or order_dropdown.get() == 'Your least streamed':
        if thirty_sec_rule:
            if order_dropdown.get() == 'Your most streamed':
                songs_to_use = pf.sort_songs_by("registered_times_played", unfucked_data, True)
            else:
                songs_to_use = pf.sort_songs_by("registered_times_played", unfucked_data, False)
        else:
            if order_dropdown.get() == 'Your most streamed':
                songs_to_use = pf.sort_songs_by("times_played", unfucked_data, True)
            else:
                songs_to_use = pf.sort_songs_by("times_played", unfucked_data, False)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, ["times_played"])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Average time listened (by %)":
        _songs_to_use = pf.sort_songs_by("average_time_listened", unfucked_data, True)

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
                song_data = pf.get_song_display_info(song_id, unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, ["times_played"])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Skips":
        songs_to_use = pf.sort_songs_by("skips", unfucked_data, True)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, ["skips"])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()
    elif order_dropdown.get() == "Chronologicaly" or order_dropdown.get() == "Chronologicaly descending":
        reverse = False
        if order_dropdown.get() == "Chronologicaly descending":
            reverse = True
        
        only_timestamps = []

        # get all timestamps in a tuple
        for song in unfucked_data:
            song_id = song["song_id"]
            timestamps = song["timestamps"]

            for timestamp in timestamps:
                only_timestamps.append((song_id, timestamp))

        # organize the timestamps
        songs_to_use = sorted(only_timestamps, key=lambda x: x[1], reverse=reverse)

        for i in range(len(songs_to_use)):
            if len(songs_analized) >= limit:
                break

            song_id = songs_to_use[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unfucked_data)

                if thirty_sec_rule and song_data["registered_times_played"] is 0:
                    continue
                    
                songs_analized.append(song_id)

                process_song(song_data, row, col, ["first/last timestamp"])

                col += 1
                if col >= songs_per_row:
                    col = 0
                    row += 1

                main_frame.update()


app.mainloop()