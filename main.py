import os
import yaml
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dataclasses import dataclass


@dataclass(frozen=True)
class Playlist:
    name: str
    url: str
    directory: str


@dataclass(frozen=True)
class PlaylistPath:
    playlist_name: str
    path: str


def load_data() -> dict:
    with open("config.yaml") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as error:
            raise error
    return data


def create_directories(paths: list[PlaylistPath]) -> None:
    for path in paths:
        try:
            os.mkdir(path.path)
        except FileExistsError:
            pass
        except OSError as error:
            print(error)


def create_directory_paths(
    root_folder: str, playlists: list[Playlist]
) -> list[PlaylistPath]:
    paths = []
    for playlist in playlists:
        try:
            path = os.path.join(root_folder, playlist.name)
            paths.append(PlaylistPath(playlist.name, path))
        except OSError as error:
            raise error
    return paths


def create_playlists(username: str, root_folder: str, spotify_client) -> list[Playlist]:
    playlists = []
    user_data = spotify_client.user_playlists(username)
    for playlist in user_data["items"]:
        name = playlist["name"]
        url = playlist["external_urls"]["spotify"]
        playlists.append(Playlist(name, url, root_folder))
    return playlists


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
            )
        )
    return new_playlists


def create_command_string(config_data: dict, playlist: Playlist) -> str:
    arguments = [
        playlist.url,
        "--m3u" if config_data["generate_m3u"] else "",
        f'--output-format {config_data["output_format"]}',
        f'--lyrics-provider {config_data["lyrics_provider"]}',
        f'--download-threads {config_data["download_threads"]}',
        f'--search-threads {config_data["search_threads"]}',
        f'--output "{playlist.directory}"',
    ]
    return f"spotdl {' '.join(arguments)}"


def download_playlists(playlists: list[Playlist], config_data: dict) -> None:
    for playlist in playlists:
        print("\n" + playlist.name)
        command = create_command_string(config_data, playlist)
        with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
            for line in process.stdout:
                print(line.decode().strip())


def check_parent_directory_exists(path: str) -> None:
    if os.path.isdir(path) is False:
        os.makedirs(path)


def validate_config_data(data: dict) -> dict:
    new_data = data.copy()

    if data["output_format"].lower() not in [
        "mp3",
        "m4a",
        "flac",
        "opus",
        "ogg",
        "wav",
    ]:
        raise Exception(
            "output_format must be of the following (mp3/m4a/flac/opus/ogg/wav)"
        )

    try:
        new_data["root_folder"] = os.path.normpath(data["root_folder"])
    except OSError as error:
        raise error

    if (
        isinstance(data["download_threads"], int) is False
        or isinstance(data["search_threads"], int) is False
    ):
        raise Exception("download_threads/search_threads must be an integer")

    if data["download_threads"] <= 0 or data["search_threads"] <= 0:
        raise Exception("download_threads/search_threads must be greater than 0")

    if data["lyrics_provider"] not in ["genius", "musixmatch"]:
        raise Exception("lyrics_provider must be 'genius' or 'musixmatch'")
    return new_data


def get_spotify_client():
    client_credentials_manager = SpotifyClientCredentials(
        client_id="c96eb3dcd29046e685a317b6c4474683",
        client_secret="c129a8a626d5475081f46d430a08a92f",
    )
    spotify_client = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager
    )
    return spotify_client


def get_playlists_to_download(playlists: list[Playlist]) -> list[Playlist]:
    playlist_names = [playlist.name for playlist in playlists]
    print("all your playlists:")
    print("\n".join(playlist_names))
    print()

    user_input = (
        input("download all playlists? ('y' for yes, 'n' to manually select) ")
        .lower()
        .strip()
    )
    if user_input in ["y", "yes"]:
        return playlists
    else:
        to_add = []
        for playlist in playlists:
            user_input = (
                input(f"download playlist: {playlist.name}? y/n (or empty to accept) ")
                .lower()
                .strip()
            )
            if user_input in ["y", "yes", ""]:
                to_add.append(playlist)
                print(f"DOWNLOADING {playlist.name}\n")
            else:
                print(f"IGNORING {playlist.name}\n")
    return to_add


def main():
    config_data = load_data()
    config_data = validate_config_data(config_data)
    spotify_client = get_spotify_client()
    all_playlists = create_playlists(
        config_data["username"], config_data["root_folder"], spotify_client
    )
    playlists_to_download = get_playlists_to_download(all_playlists)
    check_parent_directory_exists(config_data["root_folder"])
    if config_data["folder_per_playlist"] is True:
        paths = create_directory_paths(
            config_data["root_folder"], playlists_to_download
        )
        playlists_to_download = update_playlists_paths(playlists_to_download, paths)
        create_directories(paths)
    download_playlists(playlists_to_download, config_data)


if __name__ == "__main__":
    main()
