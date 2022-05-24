import yaml
import os
import sys
import spotipy
import subprocess
import fnmatch
from dataclasses import dataclass
from validate_config import check_config_data_valid
from spotipy.oauth2 import SpotifyClientCredentials
from colorama import init, Style, Fore

init(autoreset=True)


@dataclass(frozen=True)
class Playlist:
    name: str
    url: str
    path: str
    spotify_id: str
    song_count: int


@dataclass(frozen=True)
class PlaylistPath:
    playlist_name: str
    path: str


def check_config_exists() -> None:
    if os.path.isfile(os.path.join(os.getcwd(), "config.yaml")) is False:
        print(
            "'config.yaml' not found. Please restore or get from: https://github.com/g1g0byte/spotify-downloader/blob/main/config.yaml"
        )
        input("press ENTER to exit...")
        sys.exit()


def load_data() -> dict:
    with open("config.yaml") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as error:
            raise error
    return data


def normalize_root_path(path: str) -> str:
    try:
        new_path = os.path.normpath(path)
    except OSError as error:
        raise error
    return new_path


def check_root_directory_exists(path: str) -> None:
    if os.path.isdir(path) is False:
        os.makedirs(path)


def get_spotify_client() -> spotipy.Spotify:
    client_credentials_manager = SpotifyClientCredentials(
        client_id="c96eb3dcd29046e685a317b6c4474683",
        client_secret="c129a8a626d5475081f46d430a08a92f",
    )
    spotify_client = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager
    )
    return spotify_client


def create_playlists(username: str, root_folder: str, spotify_client) -> list[Playlist]:
    playlists = []
    user_data = spotify_client.user_playlists(username)
    for playlist in user_data["items"]:
        name = playlist["name"]
        url = playlist["external_urls"]["spotify"]
        spotify_id = playlist["id"]
        song_count = playlist["tracks"]["total"]
        playlists.append(Playlist(name, url, root_folder, spotify_id, song_count))
    return playlists


def get_playlists_to_download(playlists: list[Playlist]) -> list[Playlist]:
    playlist_names = [playlist.name for playlist in playlists]
    print(Style.BRIGHT + "all your playlists:")
    for i, name in enumerate(playlist_names):
        print(f"{i+1}. {name}")
    print()

    user_input = (
        input("download all playlists? ('y' for yes, 'n' to manually select) ")
        .lower()
        .strip()
    )
    print()
    if user_input in ["y", "yes"]:
        return playlists
    else:
        to_add = []
        for playlist in playlists:
            user_input = (
                input(f"download playlist: {playlist.name}? ('y': yes / 'enter': no) ")
                .lower()
                .strip()
            )
            if user_input in ["y", "yes"]:
                to_add.append(playlist)
                print(Fore.GREEN + f"DOWNLOADING {playlist.name}\n")
            else:
                print(Fore.RED + f"[bold red]IGNORING {playlist.name}[/bold red]\n")
    return to_add


def create_paths(root_folder: str, playlists: list[Playlist]) -> list[PlaylistPath]:
    paths = []
    for playlist in playlists:
        try:
            path = os.path.join(root_folder, playlist.name)
            paths.append(PlaylistPath(playlist.name, path))
        except OSError as error:
            raise error
    return paths


def update_playlists_paths(
    playlists: list[Playlist], paths: list[PlaylistPath]
) -> list[Playlist]:
    new_playlists = []
    for path in paths:
        corresponding_playlist = next(
            (playlist for playlist in playlists if playlist.name == path.playlist_name)
        )
        new_playlists.append(
            Playlist(
                corresponding_playlist.name,
                corresponding_playlist.url,
                path.path,
                corresponding_playlist.spotify_id,
                corresponding_playlist.song_count,
            )
        )
    return new_playlists


def create_directories(paths: list[PlaylistPath]) -> None:
    for path in paths:
        try:
            os.mkdir(path.path)
        except FileExistsError:
            pass
        except OSError as error:
            print(error)


def download_playlists(playlists: list[Playlist], config_data: dict) -> None:
    for playlist in playlists:
        print(Style.BRIGHT + f"{playlist.name}\n")
        command = create_command_string(config_data, playlist)
        download_playlist(command)
        display_playlist_result(playlist.path, playlist.song_count)


def create_command_string(config_data: dict, playlist: Playlist) -> str:
    arguments = [
        playlist.url,
        "--m3u" if config_data["generate_m3u"] else "",
        f'--output-format {config_data["output_format"]}',
        f'--lyrics-provider {config_data["lyrics_provider"]}',
        f'--download-threads {config_data["download_threads"]}',
        f'--search-threads {config_data["search_threads"]}',
        f'--output "{playlist.path}"',
    ]
    return f"spotdl {' '.join(arguments)}"


def download_playlist(command: str) -> None:
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        for line in process.stdout:
            try:
                print(line.decode().strip())
            except UnicodeDecodeError:
                pass


def display_playlist_result(path: str, song_count: int) -> None:
    num_songs_downloaded = get_song_count_from_disk(path)

    if num_songs_downloaded == 0:
        print(
            Fore.RED
            + f"{str(num_songs_downloaded)}/{song_count}\tno songs could be found or downloaded!"
        )
    elif num_songs_downloaded < song_count:
        percentage_downloaded = round((num_songs_downloaded / song_count) * 100)
        if percentage_downloaded < 33:
            print(
                Fore.RED
                + f"{str(num_songs_downloaded)}/{song_count}\t{percentage_downloaded}% of songs found and downloaded"
            )
        elif percentage_downloaded < 66:
            print(
                Fore.YELLOW
                + f"{str(num_songs_downloaded)}/{song_count}\t{percentage_downloaded}% of songs found and downloaded"
            )
        else:
            print(
                Fore.GREEN
                + f"{str(num_songs_downloaded)}/{song_count}\t{percentage_downloaded}% of songs found and downloaded"
            )
    else:
        print(
            Fore.GREEN
            + f"{str(num_songs_downloaded)}/{song_count}\tall songs successfully downloaded!"
        )

    print("\n\n\n")


def get_song_count_from_disk(path: str) -> int:
    count = 0
    for ext in ("*.mp3", "*.m4a", "*.flac", "*.opus", "*.ogg", "*.wav"):
        count += len(fnmatch.filter(os.listdir(path), ext))
    return count


def main():
    check_config_exists()
    config_data = load_data()
    check_config_data_valid(config_data)
    config_data["root_folder"] = normalize_root_path(config_data["root_folder"])
    check_root_directory_exists(config_data["root_folder"])
    spotify_client = get_spotify_client()

    all_playlists = create_playlists(
        config_data["username"], config_data["root_folder"], spotify_client
    )
    playlists_to_download = get_playlists_to_download(all_playlists)

    if config_data["folder_per_playlist"] is True:
        paths = create_paths(config_data["root_folder"], playlists_to_download)
        playlists_to_download = update_playlists_paths(playlists_to_download, paths)
        create_directories(paths)

    download_playlists(playlists_to_download, config_data)

    print("\n\nProgram successfully finished!")
    input("press ENTER to exit...")


if __name__ == "__main__":
    main()
