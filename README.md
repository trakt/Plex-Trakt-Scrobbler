Plex-Trakt-Scrobbler
=================================

This is a proof of concept for monitoring a Plex Media Server and scrobble the result to trakt.tv

Usage:
------------

Rename config_sample.ini to config.ini and add your username and password.
Finally launch the script with python script.py and check that you don't get any errors in the terminal.
See [Jotlab] for a more in dept article.

[Jotlab]: http://www.jotlab.com/2012/01/03/plex-trakt-a-scrobbling-love-story/

TODO:
------------
* Separate all functions
* Better error handling (eg don't die if the user is using a plugin or listening to music)
* Better logging
* Transform the script into a regular Plex plugin.
