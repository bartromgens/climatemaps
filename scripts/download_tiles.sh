#!/usr/bin/env bash

# Download tiles from openclimatemap.org server to local tiles directory

rsync -avP --delete bart@openclimatemap.org:/home/bart/climatemaps/data/tiles/ ./data/tiles/
