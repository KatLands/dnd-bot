from pymongo import MongoClient
from mongo_tracker import Tracker
from typing import List

from datetime import datetime
from enum import Enum, unique
from asyncio import TimeoutError
from discord import Embed, Intents
from discord.ext import commands

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
    db_port = int(config["db"]["port"])
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
tracker = Tracker(
    MongoClient(host=db_host, port=db_port, password=db_password)["dnd-bot"]
)


@unique
class Emojis(str, Enum):
    MONDAY = "🇲"
    TUESDAY = "🇹"
    WENDESAY = "🇼"
    THURSDAY = "🇷"
    FRIDAY = "🇫"
    SATURDAY = "🇸"
    SUNDAY = "🇺"


# Events
@bot.event
async def on_ready():
    print(f"[{startTime}] - Logged in as {bot.user.name} - {bot.user.id}")


# Commands
@bot.command()
async def config(ctx):
    my_message = await ctx.message.channel.send("Config test: Days")
    for emoji in Emojis:
        await my_message.add_reaction(emoji.value)

    def check(reaction, user):
        return user == ctx.author and any(e.value == str(reaction) for e in Emojis)

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=10.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
    else:
        await ctx.message.channel.send(f"Got reaction: {reaction}")
    finally:
        await my_message.delete()


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
    tracker.reset(ctx.guild.id)
    await ctx.message.add_reaction("✅")


@bot.command()
async def skip(ctx):
    tracker.skip(ctx.guild.id)
    await ctx.message.channel.send("Skipping this week!")


@bot.command()
async def list(ctx):
    accept, decline, dream, cancel = tracker.get_all(ctx.guild.id)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Lists",
                "fields": [
                    {"name": "Accepted", "value": plist(accept)},
                    {"name": "Declined", "value": plist(decline)},
                    {"name": "Dreamers", "value": plist(dream)},
                    {"name": "Cancelled", "value": plist(cancel)},
                ],
            }
        )
    )


# Support inv [add|remove]
@bot.group()
async def inv(ctx):
    if ctx.invoked_subcommand is None:
        if (
            len(
                (
                    inv := tracker.get_inventory_for_player(
                        ctx.guild.id, ctx.message.author
                    )
                )
            )
            == 0
        ):
            inv_message = "<< Empty >>"
        else:
            inv_message = "\n".join([f"{i['qty']}:{i['item']}" for i in inv])

        await ctx.message.channel.send(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": f"__*{ctx.message.author.name}'s Inventory:*__",
                            "value": inv_message,
                        }
                    ]
                }
            )
        )


@inv.command(name="add")
async def add(ctx):
    _, _, items = ctx.message.content.split(" ", 2)
    unpacked_items = items.split(", ")
    for pair in unpacked_items:
        qty, item = pair.split(":")
        tracker.add_to_player_inventory(ctx.guild.id, ctx.author, item, qty)
    await ctx.message.add_reaction("✅")


@inv.command(name="remove")
async def remove(ctx):
    _, _, item = ctx.message.content.split(" ", 2)
    tracker.rm_from_player_inventory(ctx.guild.id, ctx.author, item)
    await ctx.message.add_reaction("✅")


@inv.command(name="update")
async def update(ctx):
    _, _, items = ctx.message.content.split(" ", 2)
    unpacked_items = items.split(", ")
    for pair in unpacked_items:
        qty, item = pair.split(":")
        tracker.update_player_inventory(ctx.guild.id, ctx.author, item, qty)
    await ctx.message.add_reaction("✅")


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
    tracker.add_attendee_for_guild(ctx.guild.id, ctx.author)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Accepted",
                        "value": f"Thanks for confirming. See you {session_day}!",
                    },
                    {
                        "name": "Attendees",
                        "value": plist(tracker.get_attendees_for_guild(ctx.guild.id)),
                    },
                ]
            }
        )
    )
    tracker.rm_decliner_for_guild(ctx.guild.id, ctx.author)


@rsvp.command(name="decline")
async def _decline(ctx):
    """
    RSVP decline. Update attendees if needed.
    """
    tracker.add_decliner_for_guild(ctx.guild.id, ctx.author)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "fields": [
                    {"name": "Declined", "value": "No problem, see you next time!"},
                    {
                        "name": "Those that have declined",
                        "value": plist(tracker.get_decliners_for_guild(ctx.guild.id)),
                    },
                ]
            }
        )
    )
    tracker.rm_attendee_for_guild(ctx.guild.id, ctx.author)


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
    tracker.add_dreamer_for_guild(ctx.guild.id, ctx.author)
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
                        "value": plist(tracker.get_dreamers_for_guild(ctx.guild.id)),
                    },
                ]
            }
        )
    )


@vote.command(name="cancel")
async def _cancel(ctx):
    """
    Vote to cancel session.
    """
    tracker.add_canceller_for_guild(ctx.guild.id, ctx.author)
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
                        "value": plist(tracker.get_cancellers_for_guild(ctx.guild.id)),
                    },
                ]
            }
        )
    )


def plist(inlist: List) -> str:
    if len(inlist) > 0:
        return ", ".join([u["name"] for u in inlist])
    else:
        return "None"


@bot.command()
async def uptime(ctx):
    """
    Print uptime duration.
    """
    now = datetime.now().replace(microsecond=0)
    await ctx.message.channel.send(f"Up for {now - startTime}")


if __name__ == "__main__":
    # Start the bot
    bot.run(token)
