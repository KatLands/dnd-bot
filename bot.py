from helpers import Tracker
from tasks import BotTasks

from datetime import datetime
from discord.ext import commands, tasks

try:
    import configparser

    # Load config
    config = configparser.ConfigParser()
    config.read("config.ini")
    token = config["secrets"]["token"]
    session_time = config["session"]["time"]
    session_day = config["session"]["day"]
    channel_id = int(config["discord"]["channelID"])
    bot_prefix = config["discord"]["botPrefix"]
    dm_id = config["discord"]["dmID"]
except KeyError:
    # fall back to environment variables
    from os import environ

    token = environ["token"]
    session_time = environ["time"]
    session_day = environ["day"]
    channel_id = int(environ["channelID"])
    bot_prefix = environ["botPrefix"]
    dm_id = environ["dmID"]


# Bot init
description = """A bot to assist with hearding players for D&D sessions."""
bot = commands.Bot(command_prefix=bot_prefix, description=description)

# Trackers
tracker = Tracker()


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
    if tracker.is_on_rsvp_accept_list(user_name):
        await ctx.message.channel.send(
            f"You are already confirmed for this {session_day}'s session. See you at {session_time}!"
        )
    else:
        tracker.rsvp_accept_session_list.append(user_name)
        tracker.check_and_remove_from_rsvp_decline(ctx.message)
        await ctx.message.channel.send(
            f"Thank you for confirming, see you on {session_day}! Here is the list of current attendees: {tracker.rsvp_accept_session_list}"
        )
        print("Confirm list: ", tracker.rsvp_accept_session_list)
        print("Decline list: ", tracker.rsvp_decline_session_list)


@rsvp.command(name="decline")
async def _decline(ctx):
    """
    RSVP decline. Update attendees if needed.
    """
    user_name = ctx.message.author.name
    if not tracker.is_on_rsvp_decline_list(user_name):
        tracker.rsvp_decline_session_list.append(user_name)
        tracker.check_and_remove_from_rsvp_accept(ctx.message)
        await ctx.message.channel.send("No problem, see you next session!")
        print("Confirm list: ", tracker.rsvp_accept_session_list)
        print("Decline list: ", tracker.rsvp_decline_session_list)
    else:
        await ctx.message.channel.send(
            f"You are already declined for this {session_day}s session. See you next time!"
        )


# Support vote [dream|cancel]
@bot.group()
async def vote(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.message.channel.send(
            f"Please `{bot_prefix}vote dream` or `{bot_prefix}vote cancel`"
        )


@vote.command(name="dream")
async def _dream(ctx):
    """
    Vote for a dream session.
    """
    user_name = ctx.message.author.name
    tracker.alt_vote_dream_session_list.append(user_name)
    await ctx.message.channel.send(
        f"Thank you for your input, you have been added to the dream list. Currently consisting of {tracker.alt_vote_dream_session_list}"
    )
    print("Dream list: ", tracker.alt_vote_dream_session_list)


@vote.command(name="cancel")
async def _cancel(ctx):
    """
    Vote to cancel session.
    """
    user_name = ctx.message.author.name
    tracker.alt_vote_cancel_session_list.append(user_name)
    await ctx.message.channel.send(
        f"Thank you for your input, you have been added to the cancel list, currently consisting of {tracker.alt_vote_cancel_session_list}"
    )
    print("Cancel list: ", tracker.alt_vote_cancel_session_list)


# Tasks
bt = BotTasks(bot)


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
    if today == 4 and hour == 16 and mins == 1:
        await bt.every_friday(channel_id, session_day)
    elif today == 5 and hour == 20 and mins == 1:
        await bt.send_dm(dm_id, tracker)
    elif today == 6 and hour == 16 and mins == 1:
        await bt.every_sunday(channel_id)
    elif today == 6 and hour == 20 and mins == 1:
        await bt.session_decision(channel_id, tracker)


if __name__ == "__main__":
    # Start the bot
    daily_tasks.start()
    bot.run(token)
