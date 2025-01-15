import logging
import os
import subprocess

from openai import OpenAI
from yaml import Loader, load

log = logging.getLogger(__name__)


def get_transcription(link: str, gpt: OpenAI):
    """Given a youtube URL, return the transcription of the video"""

    # First we can clean up the youtube link to get the video id
    if 'youtu.be' in link:  # Mobile links
        video_id = link.split("youtu.be/")[1].split("?")[0]
    elif 'youtube.com' in link:  # Desktop links
        video_id = link.split("v=")[1].split("&")[0]
    else:
        log.error(f"Invalid youtube link: {link}")
        return "Invalid youtube link"
    formatted_link = f"https://www.youtube.com/watch?v={video_id}"

    # Then we need to download the audio file from the link
    num_tries = 0
    while num_tries < 3:
        check = download_audio(formatted_link)
        if not check:
            log.error(f"Failed to download audio from {formatted_link} after {num_tries} tries")
            if num_tries == 1:
                _ = update_yt_dlp()
            num_tries += 1
        else:
            break
    else:
        return "Failed to download the audio file"

    # Then we use the OpenAI whisper 1 model to transcribe the audio file
    audio_file = open("downloaded_audio.m4a", "rb")
    try:
        log.info("Attempting to transcribe audio file downloaded_audio.m4a")
        transcription = gpt.audio.transcriptions.create(
            model="whisper-1", file=audio_file, response_format="text"
        )
    except Exception as error:
        log.error(f"Failed to transcribe audio file downloaded_audio.m4a: {error}")
        return f"Failed to transcribe the audio file: {error}"

    # Clean up the audio file
    os.remove("downloaded_audio.m4a")

    return transcription


def update_yt_dlp():
    """Update the yt-dlp package and return whether the return code is == 0"""
    log.info("Attempting to update yt-dlp")
    output = subprocess.run(["pip", "install", "-U", "yt-dlp"])
    return output.returncode == 0


def download_audio(link: str) -> bool:
    """Given a youtube URL, download the audio of the video using a bash script
    and return whether the return code is == 0"""
    log.info(f"Attempting to download audio from {link}")
    output = subprocess.run(
        [
            "./download_audio.sh",
            f"{link}",
            "--format",
            "m4a",
            "-o",
            "downloaded_audio.m4a",
        ]
    )
    log.info(f"Got return code {output.returncode} from downloading audio")
    return output.returncode == 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with open("config.yaml", "r") as yml:
        config = load(yml, Loader=Loader)
    gpt: OpenAI = OpenAI(api_key=config["openai_api_key"])

    log.info(get_transcription("https://www.youtube.com/watch?v=FHt6glkEM9A&ab_channel=ForbesBreakingNews", gpt))
    log.info(get_transcription("https://youtu.be/FHt6glkEM9A?si=r1-07kwNLUJdlrYB", gpt))
