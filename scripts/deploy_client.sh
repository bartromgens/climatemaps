#!/usr/bin/env bash
set -e

cd client || exit
ng build
rsync -avP --delete dist/client/browser/ bart@openclimatemap.org:/home/bart/climatemaps-client
