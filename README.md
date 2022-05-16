# spotify-downloader
 
Download all your spotify playlists using [spotDL](https://github.com/spotDL/spotify-downloader) in one script

## What it does

1. Reads your Spotify playlists using your Spotify username
2. Prompts which playlists you want to download
3. Downloads the playlists, retrieving metadata for each song such as:
    - Track Name
    - Track Number
    - Album
    - Album Cover
    - Genre
    - and more!

## Installation/Setup

1. From [releases](https://github.com/g1g0byte/spotify-downloader/releases) download the latest build

2. Open `config.yaml` using your preferred text editor 
      - recommended: [Notepad++](https://notepad-plus-plus.org/)

3. Add your Spotify username which can be found at [www.spotify.com/account/overview](https://www.spotify.com/account/overview/)
```yaml
 username: 'abcdefghiklmnopqrstuvwxyz'
```

4. Add the path to the directory you wish to download your playlists
```yaml
 root_folder: 'C:\Never\Gonna\Give\You\Up'
```

5. Run `main.exe` and follow the instructions
