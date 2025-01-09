#!/bin/bash

# Expect the youtube video URL as the first argument, exit if not provided
if [ -z "$1" ]; then
    echo "Please provide the youtube video URL surrounded by quotation marks as the first argument"
    exit 1
fi

YOUTUBE_URL=$1

yt-dlp "$YOUTUBE_URL" --format m4a -o "downloaded_audio.m4a"
