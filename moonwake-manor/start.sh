#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -f assets/scene.json ]; then
    /usr/bin/python3 -m zipfile -e assets.zip .
fi
# flock prevents two desktop startup mechanisms from launching duplicate copies.
if command -v flock >/dev/null 2>&1; then
    exec 9>"${XDG_RUNTIME_DIR:-/tmp}/moonwake-$(id -u).lock"
    flock -n 9 || exit 0
fi
exec /usr/bin/python3 haunted.py "$@"
