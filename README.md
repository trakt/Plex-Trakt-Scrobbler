# Plex Trakt Scrobbler

**WARNING:** Do not use the autoscrobbling functionality if you are planning to use more than 1 client at a time.

## Installation

### Add the plugin to Plex Media Server

Download the plugin from [here](https://github.com/tester22/Plex-Trakt-Scrobbler/zipball/master). This will give you the latest version of the code.

- Extract the zipfile and copy the `Trakttv.bundle` file to your Plex Media server plugin folder
  * On OS X `~/Library/Application Support/Plex Media Server/Plug-ins`
- In your Plex client, go to `Applications` -> `Trakt.tv Scrobbler` -> `Preferences`
- Enter your [Trakt.tv](http://trakt.tv) username and password

### Set logging level in Plex Media Server

In order for the scrobbler to detect what you are playing, you will need to set the logging level in the Plex Media Server (PMS).

- Go to Plex / Web
  - Easiest way is to click on the PMS icon in the menu bar, then select `Media Manager...`
  - If you have the dock icon enabled, clicking it will bring up the Plex / Web interface.
  - Alternatively, you can visit http://localhost:32400/web, replacing the host and port if you have changed them.
- Click on `Settings` (screwdriver / wrench logo)
- Click `Show advanced settings`
- Check the box for `Plex Media Server verbose logging`
- Click `Save`

Now everything should be ready for you to start scrobbling your Movies and TV Shows to Trakt!

## Issues

The plugin is still work in progress so there may be bugs. Please report all bugs on the [Plex forum thread](http://forums.plexapp.com/index.php/topic/35626-plex-media-server-scrobbler-for-trakttv/).

Code contributions are also welcome. Submit pull requests via GitHub and they will be reviewed and merged in.
