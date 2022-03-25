from asyncio import TimeoutError
from datetime import datetime
from subprocess import check_output

import discord
from discord import Embed, app_commands
from discord.ext import tasks
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
    guild_id = int(bot_config["secrets"]["guild_id"])
    app_id = int(bot_config["secrets"]["application_id"])
    db_host = bot_config["db"]["host"]
    db_port = int(bot_config["db"]["port"])
    db_password = bot_config["db"]["password"]
    alert_time = int(bot_config["alerts"]["time"])
except KeyError:
    # Fall back to environment variables
    from os import environ

    token = environ["token"]
    guild_id = int(environ["guildID"])
    app_id = int(environ["appID"])
    db_host = environ["dbHost"]
    db_port = int(environ["dbPort"])
    db_password = environ["dbPassword"]
    alert_time = int(environ["alertTime"])

# Bot init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
# Changing the bot's "About Me" hasn't been implemented yet; use the dev portal for now #
# description = """A bot to assist with herding players for D&D sessions."""
# bot = discord.Client(description=description, intents=intents, application_id=app_id)
bot = discord.Client(intents=intents, application_id=app_id)
tree = app_commands.CommandTree(bot)
startTime = datetime.now().replace(microsecond=0)

dbh = MongoClient(host=db_host, port=db_port, password=db_password)
tracker = Tracker(dbh["dnd-bot"])


# Events
@bot.event
async def setup_hook():
    await tree.sync(guild=discord.Object(id=guild_id))  # Syncs the application commands to Discord
    print(f"Slash synced")


@bot.event
async def on_ready():
    print(f"[{startTime}] - Logged in as {bot.user.name} - {bot.user.id}")


# Commands
@tree.command(guild=discord.Object(id=guild_id))
async def status(interaction: discord.Interaction):
    """Get bot uptime, git commit id, and database status."""
    try:
        dbh.admin.command("ping")
    except ConnectionFailure:
        db_status = "offline"
    else:
        db_status = "online"
    git = check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
    now = datetime.now().replace(microsecond=0)
    await interaction.response.send_message(
        f"Up for **{now - startTime}** on `{git}`. Database is **{db_status}**."
    )


# config
@tree.command(guild=discord.Object(id=guild_id))
async def config(interaction: discord.Interaction):
    """Configure D&D meeting schedule"""
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
        guild_id=guild_id,
        dm_user=ctx.author,
        session_day=config["session-day"],
        session_time=config["session-time"],
        meeting_room=ctx.message.channel.id,
        first_alert=config["first-alert"],
        second_alert=config["second-alert"],
    )
    await interaction.response.send_message(f'Config saved!')


async def ask_for_time(interaction: discord.Interaction):
    my_message = await interaction.response.send_message("Configure time (24h HH:MM):")

    def check(m):
        return ctx.author == m.author

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
    except TimeoutError:
        await interaction.response.send_message("Fail! React faster!")
        to_return = None
    else:
        to_return = response.content.strip()
    finally:
        await my_message.delete()
        return to_return


async def ask_for_day(ctx, ask, interaction: discord.Interaction):
    my_message = await interaction.response.send_message(f"Configure: {ask}")
    for emoji in Emojis:
        await my_message.add_reaction(emoji.value)

    def check(reaction, user):
        return user == ctx.author and any(e.value == str(reaction) for e in Emojis)

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=10.0, check=check)
    except TimeoutError:
        await interaction.response.send_message("Fail! React faster!")
        to_return = None
    else:
        to_return = str(reaction)
    finally:
        await my_message.delete()
        return to_return


# uncofig
@tree.command(guild=discord.Object(id=guild_id))
async def unconfig(interaction: discord.Interaction):
    """Remove meeting configuration"""
    tracker.rm_guild_config(guild_id)
    await interaction.response.send_message("👋")


# register
@tree.command(guild=discord.Object(id=guild_id))
async def register(interaction: discord.Interaction):
    """Register yourself as a player"""
    tracker.register_player(guild_id, interaction.user)
    await interaction.response.send_message("✅")


# players
@tree.command(guild=discord.Object(id=guild_id))
async def players(interaction: discord.Interaction):
    """List all registered players"""
    players = tracker.get_players_for_guild(guild_id)
    await interaction.response.send_message(
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


# reset
@tree.command(guild=discord.Object(id=guild_id))
async def reset(interaction: discord.Interaction):
    """Reset everything"""
    tracker.reset(guild_id)
    await interaction.response.send_message("✅")


# skip
@tree.command(guild=discord.Object(id=guild_id))
async def skip(interaction: discord.Interaction):
    """Skip the meeting this week"""
    tracker.skip(guild_id)
    await interaction.response.send_message(f'Skipping this week!')


# list
@tree.command(guild=discord.Object(id=guild_id))
async def list(interaction: discord.Interaction):
    """List player statuses"""
    accept, decline, dream, cancel = tracker.get_all(guild_id)
    await interaction.response.send_message(
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


##############################################

# Support inventory [add|remove]
class Inventory(app_commands.Group):
    async def inv(self, ctx, interaction: discord.Interaction):
        if ctx.invoked_subcommand is None:
            if (
                    len(
                        (
                                inv := tracker.get_inventory_for_player(
                                    guild_id, ctx.message.author
                                )
                        )
                    )
                    == 0
            ):
                inv_message = "<< Empty >>"
            else:
                inv_message = "\n".join([f"{i['qty']}:{i['item']}" for i in inv])

            await interaction.response.send_message(
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

    @app_commands.command(description="Add an item to your inventory")
    async def add(self, interaction: discord.Interaction):
        _, _, items = ctx.message.content.split(" ", 2)
        unpacked_items = items.split(", ")
        for pair in unpacked_items:
            qty, item = pair.split(":")
            tracker.add_to_player_inventory(guild_id, ctx.author, item, qty)
        await interaction.response.send_message("✅")

    @app_commands.command(description="Remove an item from your inventory")
    async def remove(self, interaction: discord.Interaction):
        _, _, item = ctx.message.content.split(" ", 2)
        tracker.rm_from_player_inventory(guild_id, ctx.author, item)
        await interaction.response.send_message("✅")

    @app_commands.command(description="Update an item in your inventory")
    async def update(self, interaction: discord.Interaction):
        _, _, items = ctx.message.content.split(" ", 2)
        unpacked_items = items.split(", ")
        for pair in unpacked_items:
            qty, item = pair.split(":")
            tracker.update_player_inventory(guild_id, ctx.author, item, qty)
        await interaction.response.send_message("✅")


# To add the Inventory group to your tree
tree.add_command(Inventory(), guild=discord.Object(id=guild_id))


# Support rsvp [accept|decline]
class Rsvp(app_commands.Group):  # capitalizing all letters makes this break
    async def rsvp(self):
        pass

    @app_commands.command(description="Accept RSVP invitation")
    async def accept(self, interaction: discord.Interaction):
        tracker.add_attendee_for_guild(guild_id, ctx.author)
        await interaction.response.send_message(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Accepted",
                            "value": "Thanks for confirming!",
                        },
                        {
                            "name": "Attendees",
                            "value": plist(tracker.get_attendees_for_guild(guild_id)),
                        },
                    ]
                }
            )
        )
        tracker.rm_decliner_for_guild(guild_id, ctx.author)

    @app_commands.command(description="Decline RSVP invitation")
    async def decline(self, interaction: discord.Interaction):
        tracker.add_decliner_for_guild(guild_id, ctx.author)
        await interaction.response.send_message(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {"name": "Declined", "value": "No problem, see you next time!"},
                        {
                            "name": "Those that have declined",
                            "value": plist(tracker.get_decliners_for_guild(guild_id)),
                        },
                    ]
                }
            )
        )
        tracker.rm_attendee_for_guild(guild_id, ctx.author)


# To add the RSVP group to your tree
tree.add_command(Rsvp(), guild=discord.Object(id=guild_id))


# Support vote [dream|cancel]
class Vote(app_commands.Group):
    async def vote(self):
        pass

    @app_commands.command(description="Add yourself to the dreaming list")
    async def dream(self, interaction: discord.Interaction):
        tracker.add_dreamer_for_guild(guild_id, ctx.author)
        await interaction.response.send_message(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Dreaming",
                            "value": "You've been added to the dreaming list!",
                        },
                        {
                            "name": "Other dreamers",
                            "value": plist(tracker.get_dreamers_for_guild(guild_id)),
                        },
                    ]
                }
            )
        )

    @app_commands.command(description="Vote to cancel")
    async def cancel(self, interaction: discord.Interaction):
        tracker.add_canceller_for_guild(guild_id, ctx.author)
        await interaction.response.send_message(
            embed=Embed().from_dict(
                {
                    "fields": [
                        {
                            "name": "Cancelling",
                            "value": "You've voted to cancel this week.",
                        },
                        {
                            "name": "Others that have cancelled",
                            "value": plist(tracker.get_cancellers_for_guild(guild_id)),
                        },
                    ]
                }
            )
        )


# To add the Vote group to your tree
tree.add_command(Vote(), guild=discord.Object(id=guild_id))

bt = BotTasks(bot)


# @tasks.loop(hours=1)
# async def alert_dispatcher():
#     await bot.wait_until_ready()
#     if int(datetime.now().strftime("%H")) != alert_time:
#         return
#     today = datetime.now().weekday()
#     day_before, _ = adjacent_days(today)
#     for config in tracker.get_first_alert_configs(today):
#         if not tracker.is_full_group(config["guild"]):
#             await bt.first_alert(config)
#     for config in tracker.get_second_alert_configs(today):
#         if not tracker.is_full_group(config["guild"]):
#             await bt.second_alert(config)
#     for config in tracker.get_session_day_configs(today):
#         await bt.send_dm(config, tracker)
#     for config in tracker.get_session_day_configs(day_before):
#         bt.reset(config, tracker)


if __name__ == "__main__":
    # alert_dispatcher.start()
    bot.run(token)
