import os
import yaml
import subprocess
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


def create_directory_paths(root_folder: str, playlists: list[Playlist]) -> list[dict]:
    paths = []
    for playlist in playlists:
        try:
            path = os.path.join(root_folder, playlist.name)
            paths.append(PlaylistPath(playlist.name, path))
        except OSError as error:
            raise error
    return paths


def create_playlists(playlist_data: list[dict], root_folder: str) -> list[Playlist]:
    playlists = []
    for playlist in playlist_data:
        playlists.append(Playlist(playlist["name"], playlist["url"], root_folder))
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
        f'--output "{playlist.directory}"',
    ]
    return "spotdl " + " ".join(arguments)


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
    default_output_format = "mp3"
    new_data = data.copy()

    if data["output_format"].lower() not in [
        "mp3",
        "m4a",
        "flac",
        "opus",
        "ogg",
        "wav",
    ]:
        print(f'invalid output format: {data["output_format"]}')
        print(f"falling back to default output format: {default_output_format}")
        new_data["output_format"] = default_output_format

    try:
        new_data["root_folder"] = os.path.normpath(data["root_folder"])
    except OSError as error:
        raise error

    return new_data


def main():
    config_data = load_data()
    config_data = validate_config_data(config_data)
    playlists = create_playlists(config_data["playlists"], config_data["root_folder"])
    check_parent_directory_exists(config_data["root_folder"])
    if config_data["folder_per_playlist"]:
        paths = create_directory_paths(config_data["root_folder"], playlists)
        playlists = update_playlists_paths(playlists, paths)
        create_directories(paths)
    download_playlists(playlists, config_data)


if __name__ == "__main__":
    main()
