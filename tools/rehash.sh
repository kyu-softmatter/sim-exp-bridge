#!/usr/bin/env bash
# The tool `hashes.json`'s own `_comment` had been citing since the manifest
# existed, and which did not exist until 2026-09-16 -- a cited tool is a
# citation like any other, and this one resolved to nothing for the whole life
# of the file. R6's resolve branch is what made that visible; this is the
# other half of the same fix.
#
# It deliberately does NOT reimplement hashing. There is one copy of "what is
# hashed" and it is in validate.py, because two copies of a hashing recipe
# disagree in exactly the way nobody notices.
#
#   tools/rehash.sh --root am=PATH --root bd=PATH
#
# Prints the hashes.json lines to ADD for every registered path whose content
# has moved past all of its registered revisions. It writes nothing:
#
#   * the round number is yours to name -- `@r9` says which round distilled it,
#     and no tool knows that;
#   * refreshing an unsuffixed key invalidates every citation pointing at it,
#     which is the cascade R6's revision convention exists to stop.
set -euo pipefail
exec python3 "$(cd "$(dirname "$0")/.." && pwd)/validate.py" \
    --resolve --emit-registrations "$@"
