import discord
import configparser

from datetime import datetime, date
from discord.ext import commands, tasks

# Load config
config = configparser.ConfigParser()
config.read("config.ini")
token = config["secrets"]["token"]
session_time = config["session"]["time"]
session_day = config["session"]["day"]
channel_id = int(config["discord"]["channelID"])
bot_prefix = config["discord"]["botPrefix"]
dm_id = config["discord"]["dmID"]


# Bot init
description = """A bot to assist with hearding players for D&D sessions."""
bot = commands.Bot(command_prefix=bot_prefix, description=description)

# Trackers
trackers = {
    "current_date": datetime.today(),
    "rsvp_accept_session_list": [],
    "rsvp_decline_session_list": [],
    "alt_vote_dream_session_list": [],
    "alt_vote_cancel_session_list": [],
}

# Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")


# Commands
@bot.command()
async def ping(ctx):
    await ctx.message.channel.send("I'm alive!")


# Support rsvp [accept|decline]
@bot.group()
async def rsvp(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.message.channel.send(
            f"Please use either `{bot_prefix}rsvp accept` or `{bot_prefix}rsvp decline`."
        )


@rsvp.command(name="accept")
async def _accept(ctx):
    """
    RSVP accept. Update attendees if needed.
    """
    user_name = ctx.message.author.name
    if is_on_rsvp_accept_list(user_name):
        await ctx.message.channel.send(
            f"You are already confirmed for this {session_day}'s session. See you at {session_time}!"
        )
    else:
        trackers['rsvp_accept_session_list'].append(user_name)
        check_and_remove_from_rsvp_decline(ctx.message)
        await ctx.message.channel.send(
            f"Thank you for confirming, see you on {session_day}! Here is the list of current attendees: {trackers['rsvp_accept_session_list']}"
        )
        print("Confirm list: ", trackers['rsvp_accept_session_list'])
        print("Decline list: ", trackers['rsvp_decline_session_list'])


@rsvp.command(name="decline")
async def _decline(ctx):
    """
    RSVP decline. Update attendees if needed.
    """
    user_name = ctx.message.author.name
    if not is_on_rsvp_decline_list(user_name):
        trackers['rsvp_decline_session_list'].append(user_name)
        check_and_remove_from_rsvp_accept(ctx.message)
        await ctx.message.channel.send("No problem, see you next session!")
        print("Confirm list: ", trackers['rsvp_accept_session_list'])
        print("Decline list: ", trackers['rsvp_decline_session_list'])
    else:
        await ctx.message.channel.send(
            f"You are already declined for this {session_day}s session. See you next time!"
        )


# Support vote [dream|cancel]
@bot.group()
async def vote(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.message.channel.send(f"Please `{bot_prefix}vote dream` or `{bot_prefix}vote cancel`")


@vote.command(name="dream")
async def _dream(ctx):
    """
    Vote for a dream session.
    """
    user_name = ctx.message.author.name
    trackers['alt_vote_dream_session_list'].append(user_name)
    await ctx.message.channel.send(
        f"Thank you for your input, you have been added to the dream list. Currently consisting of {trackers['alt_vote_dream_session_list']}"
    )
    print("Dream list: ", trackers['alt_vote_dream_session_list'])


@vote.command(name="cancel")
async def _cancel(ctx):
    """
    Vote to cancel session.
    """
    user_name = ctx.message.author.name
    trackers['alt_vote_cancel_session_list'].append(user_name)
    await ctx.message.channel.send(
        f"Thank you for your input, you have been added to the cancel list, currently consisting of {trackers['alt_vote_cancel_session_list']}"
    )
    print("Cancel list: ", trackers['alt_vote_cancel_session_list'])


# Helpers
def is_on_rsvp_accept_list(user_name):
    """
    Check if user has signed up to attend
    the session.
    """
    return user_name in trackers['rsvp_accept_session_list']


def is_on_rsvp_decline_list(user_name):
    """
    Check if user has signed up to attend
    the session.
    """
    return user_name in trackers['rsvp_decline_session_list']


def check_and_remove_from_rsvp_accept(message):
    """
    Remove user from RSVP accept.
    """
    user_name = message.author.name
    try:
        trackers['rsvp_accept_session_list'].remove(user_name)
    except ValueError:
        pass


def check_and_remove_from_rsvp_decline(message):
    """
    Remover user from RSVP decline.
    """
    user_name = message.author.name
    try:
        trackers['rsvp_decline_session_list'].remove(user_name)
    except ValueError:
        pass


async def every_friday():
    """
    Run this task every Friday.
    """
    channel = bot.fetch_channel(channel_id)
    await channel.send(
        f"Are we good for this {session_day}'s D&D session? Please use either `{bot_prefix}rsvp accept` or `{bot_prefix}rsvp decline`."
    )

async def send_dm():
    target = await bot.fetch_user(dm_id)
    if target is None:
        print("we didn't get a user")
    else:
        await target.send(f"Confirm List: {trackers['rsvp_accept_session_list']} \n Decline list: {trackers['rsvp_decline_session_list']}")

async def every_sunday():
    """
    Run this task every {session_day}.
    """
    channel = bot.fetch_channel(channel_id)
    await channel.send(f"Game tonight @ 7:30pm. Please use either `{bot_prefix}rsvp accept` or `{bot_prefix}rsvp decline`.")


async def session_decision():
    """
    Post a warning that we do not have enough players
    for a full session. Ask for alternative plans.
    """
    channel = bot.fetch_channel(channel_id)
    if (
        len(trackers['rsvp_accept_session_list']) < 4 
        or len(trackers['rsvp_decline_session_list']) > 0
    ):
        await channel.send(
            f"Looks like we don't have all the Bardcore Ruffians available for tonight's session. \n\nWould the group like to have a dream session or cancel? Please use either `{bot_prefix}dream` or `{bot_prefix}cancel`."
        )


# Tasks
@tasks.loop(minutes=1)
async def daily_tasks():
    """
    Ensure our daily tasks get done.
    """
    await bot.wait_until_ready()
    # weekday returns day of week from 0-6 where monday is 0
    today = datetime.now().weekday()
    # string format time %H returns the 24 hour time in string format
    hour = int(datetime.now().strftime("%H"))
    mins = int(datetime.now().strftime("%M"))
    if today == 4 and hour == 12 and mins == 1:
        await every_friday()
    elif today == 5 and hour == 16 and mins == 1:
        await send_dm()
    elif today == 6 and hour == 12 and mins == 1:
        await every_sunday()
    elif today == 6 and hour == 16 and mins == 1:
        await session_decision()


if __name__ == "__main__":
    # Start the bot
    daily_tasks.start()
    bot.run(token)
