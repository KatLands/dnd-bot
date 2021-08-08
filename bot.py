import redis

from helpers import Tracker
from tasks import BotTasks
from typing import List

from os import execv
from sys import argv, executable
from datetime import datetime
from discord import Embed, Intents
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
    db_host = config["db"]["host"]
    db_port = config["db"]["port"]
    db_password = config["db"]["password"]
except KeyError:
    # fall back to environment variables
    from os import environ

    token = environ["token"]
    session_time = environ["time"]
    session_day = environ["day"]
    channel_id = int(environ["channelID"])
    bot_prefix = environ["botPrefix"]
    dm_id = environ["dmID"]
    db_host = environ["dbHost"]
    db_port = environ["dbPort"]
    db_password = environ["dbPassword"]


# Bot init
intents = Intents.default()
intents.members = True
description = """A bot to assist with hearding players for D&D sessions."""
bot = commands.Bot(command_prefix=bot_prefix, description=description, intents=intents)
startTime = datetime.now().replace(microsecond=0)


# Trackers
db = redis.Redis(
    host=db_host, port=db_port, password=db_password, decode_responses=True
)
tracker = Tracker(db)


# Events
@bot.event
async def on_ready():
    print(f"[{startTime}] - Logged in as {bot.user.name} - {bot.user.id}")


# Commands
@bot.command()
async def ping(ctx):
    await ctx.message.channel.send("I'm alive!")


@bot.command()
async def commands(ctx):
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Available Commands",
                "fields": [
                    {"name": cmd.name, "value": f"`{cmd.name}`"} for cmd in bot.commands
                ],
            }
        )
    )


@bot.command()
async def reset(ctx):
    tracker.reset()
    await ctx.message.channel.send("Tracking reset!")


@bot.command()
async def skip(ctx):
    tracker.skip()
    await ctx.message.channel.send("Skipping this week!")


@bot.command()
async def list(ctx):
    accept, decline, dream, cancel, is_skip = tracker.get_all()
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Lists",
                "fields": [
                    {"name": "Accepted", "value": plist(accept)},
                    {"name": "Declined", "value": plist(decline)},
                    {"name": "Dreamers", "value": plist(dream)},
                    {"name": "Cancelled", "value": plist(cancel)},
                    {"name": "Skipping?", "value": str(is_skip)},
                ],
            }
        )
    )


@bot.command()
async def add(ctx):
    await ctx.message.channel.send(
        embed = Embed.from_dict(
            {
                "fields": [
                    {
                        "name": "Enter items to add to personal inventory:",
                        "value": "\u200b"
                    }
                ]
            }
        )
    )
    add_to = await bot.wait_for('message', timeout = 60 )
    if add_to:
        tracker.add_inv(add_to.content)


@bot.command()
async def remove(ctx):
    await ctx.message.channel.send(
        embed = Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Enter items to remove from personal inventory:",
                        "value": "\u200b"
                    }
                ]
            }
        )
    )
    remove_from = await bot.wait_for("message", timeout = 60)
    if remove_from:
        tracker.remove_inv(remove_from.content)


@bot.command()
async def inv(ctx):
    await ctx.message.channel.send(
        embed = Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Inventory",
                        "value": plist(tracker.get_inv())
                    }
                ]    
            }
        )
    )


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
    if tracker.add_attendee(user_name):
        await ctx.message.channel.send(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Accepted",
                            "value": f"Thanks for confirming. See you {session_day}!",
                        },
                        {"name": "Attendees", "value": plist(tracker.get_attendees())},
                    ]
                }
            )
        )
    else:
        await ctx.message.channel.send(
            f"You are already confirmed for this {session_day}'s session. See you at {session_time}!"
        )
    tracker.remove_decliner(user_name)


@rsvp.command(name="decline")
async def _decline(ctx):
    """
    RSVP decline. Update attendees if needed.
    """
    user_name = ctx.message.author.name
    if tracker.add_decliner(user_name):
        await ctx.message.channel.send(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {"name": "Declined", "value": "No problem, see you next time!"},
                        {
                            "name": "Those that have declined",
                            "value": plist(tracker.get_decliners()),
                        },
                    ]
                }
            )
        )
    else:
        await ctx.message.channel.send(
            f"You are already declined for this {session_day}s session. See you next time!"
        )
    tracker.remove_attendee(user_name)


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
    if tracker.add_dreamer(user_name):
        await ctx.message.channel.send(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Dreaming",
                            "value": "You've been added to the dreaming list!",
                        },
                        {
                            "name": "Other dreamers",
                            "value": plist(tracker.get_dreamers()),
                        },
                    ]
                }
            )
        )
    else:
        await ctx.message.channel.send("You're already a dreamer!")


@vote.command(name="cancel")
async def _cancel(ctx):
    """
    Vote to cancel session.
    """
    user_name = ctx.message.author.name
    if tracker.add_canceller(user_name):
        await ctx.message.channel.send(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Cancelling",
                            "value": "You've voted to cancel this week.",
                        },
                        {
                            "name": "Others that have cancelled",
                            "value": plist(tracker.get_cancellers()),
                        },
                    ]
                }
            )
        )
    else:
        await ctx.message.channel.send("You've already voted to cancel.")


def plist(inlist: List) -> str:
    if len(inlist) > 0:
        return ", ".join(inlist)
    return "None"


@bot.command()
async def restart(ctx):
    """
    Restart the bot.
    """
    await ctx.message.add_reaction("👍")
    execv(executable, ["python3"] + argv)


@bot.command()
async def uptime(ctx):
    """
    Print uptime duration.
    """
    now = datetime.now().replace(microsecond=0)
    await ctx.message.channel.send(f"Up for {now - startTime}")


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
    if today == 0 and hour == 1 and mins == 1:
        await bt.reset_lists(channel_id, tracker)
    elif tracker.isSkip():
        return
    elif today == 4 and hour == 12 and mins == 1:
        await bt.every_friday(channel_id, session_day)
    elif today == 5 and hour == 16 and mins == 1:
        await bt.send_dm(dm_id, tracker)
    elif today == 6 and hour == 12 and mins == 1:
        await bt.every_sunday(channel_id, tracker)
    elif today == 6 and hour == 16 and mins == 1:
        await bt.session_decision(channel_id, tracker)


if __name__ == "__main__":
    # Start the bot
    daily_tasks.start()
    bot.run(token)
