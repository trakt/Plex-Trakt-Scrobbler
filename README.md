# trakt (for Plex)

[![](https://img.shields.io/scrutinizer/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)]() [![](https://img.shields.io/scrutinizer/coverage/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)]() [![](https://img.shields.io/scrutinizer/build/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)]() [![](https://img.shields.io/github/issues/trakt/Plex-Trakt-Scrobbler.svg?style=flat-square)](https://github.com/trakt/Plex-Trakt-Scrobbler/issues) [![](https://img.shields.io/github/release/trakt/Plex-Trakt-Scrobbler.svg?style=flat-square)](https://github.com/trakt/Plex-Trakt-Scrobbler/releases)

### Links

 - [Configuration](https://github.com/fuzeman/Plex-Trakt-Scrobbler/wiki/Configuration) *(outdated - some options might be renamed or missing)*
 - [Contributors](https://github.com/trakt/Plex-Trakt-Scrobbler/graphs/contributors)
 - [Credits](Trakttv.bundle/CREDITS.md) *(for other resources)*
 - [Issues](https://github.com/trakt/Plex-Trakt-Scrobbler/issues)

## Installation

### Download

Download the plugin from one of the following branches

 * **[master (stable)](https://github.com/trakt/Plex-Trakt-Scrobbler/archive/master.zip)**
 * [beta](https://github.com/trakt/Plex-Trakt-Scrobbler/archive/beta.zip)
 * *[develop](https://github.com/trakt/Plex-Trakt-Scrobbler/archive/develop.zip)*

### Install

Install the bundle by extracting the zip and copying the `Trakttv.bundle` folder to your Plex Media server `Plug-ins` folder

**OS X**
```
~/Library/Application Support/Plex Media Server/Plug-ins
```

**Linux**
```
/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins
```

**Windows XP**
```
C:\Documents and Settings\[username]\Local Settings\Application Data\Plex Media Server\Plug-ins
```

**Windows Vista (and later)**
```
C:\Users\[username]\AppData\Local\Plex Media Server\Plug-ins
```

### Setup

1. In Plex/Web, navigate to `Channels -> trakt -> Settings`
2. Authentication
    1. Visit https://trakt.tv/pin/478, login to trakt.tv and approve the application
    2. Enter the displayed pin into the ```Authentication PIN``` option
3. Enable automatic scrobbling by ticking the ```Scrobble``` option
3. *(optional) If you have multiple users on your server, enter your plex.tv username in ```Global Filter - Users``` to ensure only your watching activity is scrobbled*