#!/bin/bash

echo "Removing"
rm -r ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/Trakttv.bundle
echo "Copy new version"
cp -r Trakttv.bundle ~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/
echo "Done!"