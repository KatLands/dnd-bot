from asyncio import TimeoutError
from datetime import datetime
from subprocess import check_output

from discord.ext import commands, tasks
from discord import Embed, Intents
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from tasks import BotTasks
from helpers import adjacent_days, plist, Weekdays, Emojis
from mongo_tracker import Tracker

try:
    import configparser

    # Load config
    bot_config = configparser.ConfigParser()
    bot_config.read("config.ini")
    token = bot_config["secrets"]["token"]
    bot_prefix = bot_config["discord"]["botPrefix"]
    db_host = bot_config["db"]["host"]
    db_port = int(bot_config["db"]["port"])
    db_password = bot_config["db"]["password"]
    alert_time = int(bot_config["alerts"]["time"])
except KeyError:
    # Fall back to environment variables
    from os import environ

    token = environ["token"]
    bot_prefix = environ["botPrefix"]
    db_host = environ["dbHost"]
    db_port = int(environ["dbPort"])
    db_password = environ["dbPassword"]
    alert_time = int(environ["alertTime"])


# Bot init
intents = Intents.default()
intents.members = True
description = """A bot to assist with hearding players for D&D sessions."""
bot = commands.Bot(command_prefix=bot_prefix, description=description, intents=intents)
startTime = datetime.now().replace(microsecond=0)

dbh = MongoClient(host=db_host, port=db_port, password=db_password)
tracker = Tracker(dbh["dnd-bot"])


# Events
@bot.event
async def on_ready():
    print(f"[{startTime}] - Logged in as {bot.user.name} - {bot.user.id}")


# Commands
@bot.command()
async def status(ctx):
    try:
        dbh.admin.command("ping")
    except ConnectionFailure:
        db_status = "offline"
    else:
        db_status = "online"
    git = check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
    now = datetime.now().replace(microsecond=0)
    await ctx.message.channel.send(
        f"Up for **{now - startTime}** on `{git}`. Database is **{db_status}**."
    )


@bot.command()
async def config(ctx):
    questions = ["session day", "first alert", "second alert"]
    answers = [await ask_for_day(ctx, q) for q in questions]

    def map_emoji_to_day_value(emoji):
        for e in Emojis:
            if e.value == emoji:
                return Weekdays[e.name].value

    mapped_answers = [map_emoji_to_day_value(a) for a in answers]
    config = {
        questions[i].replace(" ", "-", 1): mapped_answers[i]
        for i in range(len(mapped_answers))
    }
    config["session-time"] = await ask_for_time(ctx)
    tracker.create_guild_config(
        guild_id=ctx.guild.id,
        dm_user=ctx.author,
        session_day=config["session-day"],
        session_time=config["session-time"],
        meeting_room=ctx.message.channel.id,
        first_alert=config["first-alert"],
        second_alert=config["second-alert"],
    )
    await ctx.message.channel.send("Config saved!")


async def ask_for_time(ctx):
    my_message = await ctx.message.channel.send("Configure time (24h HH:MM):")

    def check(m):
        return ctx.author == m.author

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
        to_return = None
    else:
        to_return = response.content.strip()
    finally:
        await my_message.delete()
        return to_return


async def ask_for_day(ctx, ask):
    my_message = await ctx.message.channel.send(f"Configure: {ask}")
    for emoji in Emojis:
        await my_message.add_reaction(emoji.value)

    def check(reaction, user):
        return user == ctx.author and any(e.value == str(reaction) for e in Emojis)

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=10.0, check=check)
    except TimeoutError:
        await ctx.message.channel.send("Fail! React faster!")
        to_return = None
    else:
        to_return = str(reaction)
    finally:
        await my_message.delete()
        return to_return


@bot.command()
async def register(ctx):
    tracker.register_player(ctx.guild.id, ctx.author)
    await ctx.message.add_reaction("✅")


@bot.command()
async def unregister(ctx):
    tracker.unregister_player(ctx.guild.id, ctx.author)
    await ctx.message.add_reaction("✅")


@bot.command()
async def players(ctx):
    players = tracker.get_players_for_guild(ctx.guild.id)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "title": "Registered Players",
                "fields": [
                    {"name": player["name"], "value": f"ID: {player['id']}"}
                    for player in players
                ],
            }
        )
    )


@bot.command()
async def cmds(ctx):
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
    tracker.add_attendee_for_guild(ctx.guild.id, ctx.author)
    await ctx.message.channel.send(
        embed=Embed().from_dict(
            {
                "fields": [
                    {
                        "name": "Accepted",
                        "value": "Thanks for confirming!",
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


bt = BotTasks(bot)


@tasks.loop(hours=1)
async def alert_dispatcher():
    await bot.wait_until_ready()
    if int(datetime.now().strftime("%H")) != alert_time:
        return
    today = datetime.now().weekday()
    day_before, _ = adjacent_days(today)
    for config in tracker.get_first_alert_configs(today):
        if not tracker.is_full_group(config["guild"]):
            await bt.first_alert(config)
    for config in tracker.get_second_alert_configs(today):
        if not tracker.is_full_group(config["guild"]):
            await bt.second_alert(config)
    for config in tracker.get_session_day_configs(today):
        await bt.send_dm(config, tracker)
    for config in tracker.get_session_day_configs(day_before):
        if not tracker.is_full_group(config["guild"]):
            bt.reset(config, tracker)


if __name__ == "__main__":
    alert_dispatcher.start()
    bot.run(token)
