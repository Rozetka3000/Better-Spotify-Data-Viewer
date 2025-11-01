import customtkinter as ctk
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import processFunctions as pf
import base64
from requests import post
import os

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

jsonData = None
unworked_data = None

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
                print("hui")
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
order_dropdown = ctk.CTkComboBox(settings_frame, values=["Chronologicaly", "Chronologicaly descending", "Your most streamed", "Your least streamed"],)
order_dropdown.set("Chronologicaly")
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

    print(thirty_sec_rule)
    print(order_dropdown.get())
    print(len(unworked_data))
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

def process_song(song_data, row, col):
    song_frame = ctk.CTkFrame(main_frame)
    song_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    song_info = f"Song name: {song_data['name']}\nArtists: {song_data['artists']}\nTimes played: {song_data['times_played']}"
    song_label = ctk.CTkLabel(song_frame, text=song_info, font=("Arial", 14))  # song_frame as parent!

    song_image = pf.image_from_url(song_data["cover_url"], ctk, size=(200, 200))
    song_image_label = ctk.CTkLabel(song_frame, image=song_image, text="")  # song_frame as parent!

    song_label.pack(pady=10)
    song_image_label.pack(pady=10)

def initialize_song_page():
    songs_analized = []
    row = 0
    col = 0

    if order_dropdown.get() == "Chronologicaly":
        for i in range(len(unworked_data)):
            if len(songs_analized) >= limit:
                break

            song_id = unworked_data[i]["spotify_track_uri"]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unworked_data, thirty_sec_rule)

                if song_data["times_played"] is not 0:
                    songs_analized.append(song_id)

                    process_song(song_data, row, col)

                    col += 1
                    if col >= songs_per_row:
                        col = 0
                        row += 1

                    main_frame.update()
    elif order_dropdown.get() == "Chronologicaly descending":
        for i in range(len(unworked_data)-1, -1, -1):
            if len(songs_analized) >= limit:
                break

            song_id = unworked_data[i]["spotify_track_uri"]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unworked_data, thirty_sec_rule)
                
                if song_data["times_played"] is not 0:
                    songs_analized.append(song_id)

                    process_song(song_data, row, col)

                    col += 1
                    if col >= songs_per_row:
                        col = 0
                        row += 1

                    main_frame.update()
    elif order_dropdown.get() == "Your most streamed":
        sorted_songs_crescator = sorted_songs(True)

        for i in range(len(sorted_songs_crescator)-1):
            if len(songs_analized) >= limit:
                break

            song_id = sorted_songs_crescator[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unworked_data, thirty_sec_rule)
                
                if song_data["times_played"] != 0:
                    songs_analized.append(song_id)

                    process_song(song_data, row, col)

                    col += 1
                    if col >= songs_per_row:
                        col = 0
                        row += 1

                    main_frame.update()
    elif order_dropdown.get() == "Your least streamed":
        sorted_songs_crescator = sorted_songs(True)
        for i in range(len(sorted_songs_crescator)-1, -1, -1):
            if len(songs_analized) >= limit:
                break

            song_id = sorted_songs_crescator[i][0]

            if song_id not in songs_analized:
                song_data = pf.get_song_display_info(song_id, unworked_data, thirty_sec_rule)
                
                if song_data["times_played"] != 0:
                    songs_analized.append(song_id)

                    process_song(song_data, row, col)

                    col += 1
                    if col >= songs_per_row:
                        col = 0
                        row += 1

                    main_frame.update()
    else:
        print("You fucking moron")

app.mainloop()