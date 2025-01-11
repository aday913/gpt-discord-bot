import logging
import json

import discord
from openai import OpenAI
from yaml import Loader, load

from utils.function_calling import get_transcription
from utils.utils import (
    get_gpt,
    get_tools,
    format_user_query,
    handle_thread_message,
    call_gpt,
    send_large_message,
)

log = logging.getLogger(__name__)

# Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

with open("config.yaml", "r") as yml:
    config = load(yml, Loader=Loader)
gpt: OpenAI = get_gpt(config["openai_api_key"])

thread_conversation_history = {}

tools = get_tools()


@client.event
async def on_ready():
    """Called when the bot is ready and able to be used"""
    log.info(f"Logged in as {client.user}")


@client.event
async def on_thread_create(thread):
    """Log thread creation and add thread ID to history"""
    log.info(f"Thread {thread.name} with id {thread.id} created at {thread.created_at}")
    thread_conversation_history[thread.id] = []


@client.event
async def on_message(message: discord.Message):
    """Handle all messages in the server, only responding to ones where the bot is mentioned.

    The bot can either be mentioned in a general text channel (but does not remember chat
    history) or in a public/private thread (which retains chat history for context)"""
    if message.author == client.user:  # Prevent bot responding to itself
        return

    # Mention-based interaction
    if not client.user.mentioned_in(message):
        return

    # Instantiate a "none" thread id for now
    thread_id = None

    global thread_conversation_history

    # Format the user's question to ask for markdown, separate large blocks, etc.
    user_query = format_user_query(message, client)

    # If the message comes from a thread, we need to grab the ai chat history
    if message.channel.type in [
        discord.ChannelType.public_thread,
        discord.ChannelType.private_thread,
    ]:

        # TODO: use previous messages from the thread to build history rather than keeping it saved?
        # previous_messages = [i.content async for i in message.channel.history(limit=100)
        # log.info(f'Previous messages: {previous_messages}')

        user_query = handle_thread_message(
            message, user_query, thread_conversation_history
        )
        thread_id = message.channel.id

    # Get gpt's response
    response = await call_gpt(
        user_query, thread_id, gpt, thread_conversation_history, tools
    )
    if response is None:
        response = (
            "I'm sorry, I couldn't generate a response for you. Please try again later"
        )

    # If the response asks for a tool call, we need to interpret the tool call and respond accordingly
    if response.tool_calls:
        await message.channel.send(
            "I am calling a tool for you, please wait a bit (it may take a minute)"
        )
        tool_call_json = response.tool_calls[0]
        log.info(f"Tool call: {tool_call_json}")
        arguments = json.loads(tool_call_json.function.arguments)
        function_name: str = tool_call_json.function.name
        if function_name == "get_transcription":
            transcription = get_transcription(arguments.get("link"), gpt)
            resulting_content = json.dumps(
                {"link": arguments.get("link"), "transcription": transcription}
            )
        resulting_message = {
            "role": "tool",
            "content": resulting_content,
            "tool_call_id": tool_call_json.id,
        }
        response = await call_gpt(
            user_query + [response] + [resulting_message],
            thread_id,
            gpt,
            thread_conversation_history,
            tools,
        )

    # If the message isn't too big we just send it. Otherwise, parse it accordingly
    if thread_id:
        thread_conversation_history[thread_id].append(response)


    text: str = response.content
    if len(text) < 1900:
        await message.channel.send(text)
        return
    else:
        await send_large_message(text, message)
        return


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    log = logging.getLogger(__name__)

    with open("config.yaml", "r") as yml:
        config = load(yml, Loader=Loader)
    client.run(config["discord_bot_token"])
