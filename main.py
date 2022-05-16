import os
import sys
import yaml
import spotipy
import fnmatch
import subprocess
from dataclasses import dataclass
from spotipy.oauth2 import SpotifyClientCredentials


class ConfigError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


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


def create_paths(root_folder: str, playlists: list[Playlist]) -> list[PlaylistPath]:
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
        spotify_id = playlist["id"]
        song_count = playlist["tracks"]["total"]
        playlists.append(Playlist(name, url, root_folder, spotify_id, song_count))
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
                corresponding_playlist.spotify_id,
                corresponding_playlist.song_count,
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
        f'--output "{playlist.path}"',
    ]
    return f"spotdl {' '.join(arguments)}"


def download_playlist(command: str, name: str) -> None:
    print("\n" + name)
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        for line in process.stdout:
            try:
                print(line.decode().strip())
            except UnicodeDecodeError:
                pass


def get_song_count_from_disk(path: str) -> int:
    count = 0
    for ext in ("*.mp3", "*.m4a", "*.flac", "*.opus", "*.ogg", "*.wav"):
        count += len(fnmatch.filter(os.listdir(path), ext))
    return count


def download_playlists(playlists: list[Playlist], config_data: dict) -> None:
    for playlist in playlists:
        command = create_command_string(config_data, playlist)
        download_playlist(command, playlist.name)

        num_songs_downloaded = get_song_count_from_disk(playlist.path)
        if num_songs_downloaded < playlist.song_count:
            print(
                f"{str(num_songs_downloaded)}/{playlist.song_count} songs found and downloaded"
            )
        else:
            print("all songs successfully downloaded!")

        print("\n\n\n")


def check_root_directory_exists(path: str) -> None:
    if os.path.isdir(path) is False:
        os.makedirs(path)


def normalize_root_path(path: str) -> str:
    try:
        new_path = os.path.normpath(path)
    except OSError as error:
        raise error
    return new_path


def get_spotify_client() -> spotipy.Spotify:
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


def check_config_data_valid(data: dict) -> None:
    try:
        if data["username"] is None or data["username"].strip() == "":
            raise ConfigError("'username' in config.yaml is required")
        elif isinstance(data["username"], str) is False:
            raise ConfigError("'username' in config.yaml must be a string")
        elif len(data["username"]) != 25:
            raise ConfigError("'username' in config.yaml should be 25 characters long")

        if data["root_folder"] is None or data["root_folder"].strip() == "":
            raise ConfigError("'root_folder' in config.yaml is required")
        elif isinstance(data["root_folder"], str) is False:
            raise ConfigError("'root_folder' in config.yaml must be a string")

        if data["output_format"] is None or data["output_format"].strip() == "":
            raise ConfigError("'output_format' in config.yaml is required")
        elif data["output_format"].lower() not in [
            "mp3",
            "m4a",
            "flac",
            "opus",
            "ogg",
            "wav",
        ]:
            raise ConfigError(
                "'output_format' in config.yaml must be of the following (mp3/m4a/flac/opus/ogg/wav)"
            )

        if data["download_threads"] is None or data["search_threads"] is None:
            raise ConfigError(
                "'download_threads'/'search_threads' in config.yaml is required"
            )
        elif (
            isinstance(data["download_threads"], int) is False
            or isinstance(data["search_threads"], int) is False
        ):
            raise ConfigError(
                "'download_threads'/'search_threads' in config.yaml must be an integer"
            )

        elif data["download_threads"] <= 0 or data["search_threads"] <= 0:
            raise ConfigError(
                "'download_threads'/'search_threads' in config.yaml must be greater than 0"
            )

        if data["lyrics_provider"] not in ["genius", "musixmatch"]:
            raise ConfigError(
                "'lyrics_provider' in config.yaml must be 'genius' or 'musixmatch'"
            )

    except ConfigError as e:
        print(e)
        input("press ENTER to exit...")
        sys.exit()


def main():
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


if __name__ == "__main__":
    main()
