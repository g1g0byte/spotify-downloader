import sys


class ConfigError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


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
