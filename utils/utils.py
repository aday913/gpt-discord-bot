import logging

import discord
from openai import OpenAI
from yaml import Loader, load

log = logging.getLogger(__name__)


# GPT client
def get_gpt(api_key):
    return OpenAI(api_key=api_key)


def format_user_query(message: discord.Message, client: discord.Client) -> list:
    """Given a message from a user for gpt, format it to ask gpt to format
    in markdown and separate response into smaller chunks"""
    user_query = message.content.split(f"<@{client.user.id}> ")[1]
    user_query = (
        user_query
        + ". Format your response to be in markdown without any '```' wrappers. \
        Do not provide anything but the markdown response itself. \
        In addition, I am aware that you are an AI, so you do not need to mention that. \
        Do not give warnings or notes about how the data may not be up to date or that you are an AI. \
        If your resposne is longer than 1900 characters, \
        please separate each ~1200 character blocks with a newline character"
    )
    formatted_query = {"role": "user", "content": user_query}
    log.info(
        f"GPT bot mentioned, got prompt from user {message.author}:\n {user_query}"
    )
    return [formatted_query]


def handle_thread_message(
    message: discord.Message, user_query: list, thread_conversation_history: dict
) -> list:
    """If a message comes from a thread, the method grabs all of the previous messages sent to use
    as context in the gpt query"""
    thread_id = message.channel.id
    if thread_id not in list(thread_conversation_history.keys()):
        log.info(f"Thread ID {thread_id} not found in history, adding")
        thread_conversation_history[thread_id] = []
    thread_conversation_history[thread_id].append(user_query[0])
    return thread_conversation_history[thread_id]


async def send_large_message(gpt_response: str, message: discord.Message):
    """Method splits a gpt response into ~1500 character chunks due to discord's
    message length limit. Each chunk is sent as a message separately"""
    temp_message = ""
    split_response = gpt_response.split("\n")
    for i in range(len(split_response)):
        temp_message = temp_message + f"{split_response[i]}\n"
        if len(temp_message) > 1500:
            await message.channel.send(temp_message)
            temp_message = ""
    if temp_message != "":
        await message.channel.send(temp_message)
    return


async def call_gpt(
    prompt: list, thread_id: int | None, gpt: OpenAI, thread_conversation_history: dict
) -> str | None:
    """Given a prompt (either a direct prompt string or a list of chat history including the
    new message), the method will send the prompt to gpt and return the response text
    """
    log.info(f"Using the following prompt when calling gpt api: {prompt}")
    response = gpt.chat.completions.create(model="gpt-4o", messages=prompt)
    log.info(f"Got the following candidates from GPT:\n {response.choices}")
    first_candidate = response.choices[0].message
    if thread_id:
        thread_conversation_history[thread_id].append(first_candidate)
    return first_candidate.content
