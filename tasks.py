from typing import Any

import helpers
from helpers import plist


class BotTasks:
    def __init__(self, bot):
        self.bot = bot

    async def first_alert(self, config, unanswered) -> None:
        channel: Any = await self.bot.fetch_channel(config["config"]["meeting-room"])
        at_ids = list(map(helpers.callable_username, unanswered))

        await channel.send(
            f"{', '.join(at_ids)} Are we good for our D&D session? Please use either `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def second_alert(self, config, unanswered) -> None:
        channel: Any = await self.bot.fetch_channel(config["config"]["meeting-room"])
        at_ids = list(map(helpers.callable_username, unanswered))

        await channel.send(
            f"Please RSVP: {','.join(at_ids)} `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def session_alert(self, config) -> None:
        channel: Any = await self.bot.fetch_channel(config["config"]["meeting-room"])
        await channel.send(
            f"Game tonight! Please RSVP: `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def cancel_alert_msg(self, config) -> None:
        channel: Any = await self.bot.fetch_channel(config["config"]["meeting-room"])
        await channel.send(f"Reminder, the upcoming session was cancelled!")

    async def send_dm(self, config, tracker) -> None:
        dm: Any = await self.bot.fetch_user(config["config"]["session-dm"]["id"])
        if dm is None:
            print(f"We didn't get a user when using config: {config}")
        else:
            await dm.send(
                f"Confirm List: {plist(tracker.get_attendees_for_guild(config['guild']))}\nDecline list: {plist(tracker.get_decliners_for_guild(config['guild']))}"
            )

    def reset(self, config, tracker) -> None:
        tracker.reset(config["guild"])
