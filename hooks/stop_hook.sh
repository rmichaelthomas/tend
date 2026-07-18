#!/usr/bin/env bash
input=$(cat)
transcript=$(echo "$input" | jq -r '.transcript_path // empty')
[ -n "$transcript" ] && tend tick --transcript "$transcript" &
exit 0
