import logging
import json
import subprocess

from openai import OpenAI

log = logging.getLogger(__name__)

def get_transcription(link: str) -> str:
    """Given a youtube URL, return the transcription of the video"""
    return f"{link}"

def download_audio(link: str) -> bool:
    """Given a youtube URL, download the audio of the video using a bash script"""
    log.info(f"Attempting to download audio from {link}")
    output = subprocess.run(["./download_audio.sh", f"{link}", "--format", "m4a", "-o", "downloaded_audio.m4a"])
    log.info(f"Got return code {output.returncode} from downloading audio")
    return output.returncode == 0

if __name__ == "__main__":
    download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley")
