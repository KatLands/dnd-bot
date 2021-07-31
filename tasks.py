import helpers
from helpers import Tracker
from typing import Any
from discord import Role


class BotTasks:
    def __init__(self, bot):
        self.bot = bot

    async def every_friday(self, channel_id: int, session_day: str) -> None:
        """
        Run this task every Friday.
        """
        channel: Any = await self.bot.fetch_channel(channel_id)
        await channel.send(
            f"Are we good for this {session_day}'s D&D session? Please use either `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def send_dm(self, dm_id: int, tracker) -> None:
        target: Any = await self.bot.fetch_user(dm_id)
        if target is None:
            print("we didn't get a user")
        else:
            await target.send(
                f"Confirm List: {', '.join(tracker.get_attendees())}\nDecline list: {', '.join(tracker.get_decliners())}"
            )

    @staticmethod
    async def check_rsvp_full(tracker, guild) -> bool:
        member_count = len([member for member in guild.members if not member.bot])
        print(guild.members)
        print(len(tracker.get_attendees()))

        if member_count == len(tracker.get_attendees()):
            return True
        else:
            return False


    async def every_sunday(self, channel_id: int, tracker) -> None:
        """
        Run this task every {session_day}.
        """
        channel: Any = await self.bot.fetch_channel(channel_id)
        if await self.check_rsvp_full(tracker, channel.guild):
            await channel.send(
                "We have a full group for tonight's game. See you at 7:30pm!"
            )
        else:
            await channel.send(
                f"Game tonight @ 7:30pm. Please use either `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
            )

    async def session_decision(
        self, channel_id: int, tracker: "helpers.Tracker"
    ) -> None:
        """
        Post a warning that we do not have enough players
        for a full session. Ask for alternative plans.
        """
        channel: Any = await self.bot.fetch_channel(channel_id)
        if len(tracker.get_attendees()) < 4 or len(tracker.get_decliners()) > 0:
            await channel.send(
                f"Looks like we don't have all the Bardcore Ruffians available for tonight's session. \n\nWould the group like to have a dream session or cancel? Please use either `{self.bot.command_prefix}vote dream` or `{self.bot.command_prefix}vote cancel`."
            )

    async def reset_lists(self, channel_id: int, tracker: "helpers.Tracker") -> None:
        channel: Any = await self.bot.fetch_channel(channel_id)
        tracker.reset()
        await channel.send("Weekly reset complete!")
