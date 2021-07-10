class BotTasks:
    def __init__(self, bot):
        self.bot = bot

    async def every_friday(self, channel_id, session_day):
        """
        Run this task every Friday.
        """
        channel = await self.bot.fetch_channel(channel_id)
        await channel.send(
            f"Are we good for this {session_day}'s D&D session? Please use either `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def send_dm(self, dm_id, tracker):
        target = await self.bot.fetch_user(dm_id)
        if target is None:
            print("we didn't get a user")
        else:
            await target.send(
                f"Confirm List: {tracker.rsvp_accept_session_list} \n Decline list: {tracker.rsvp_decline_session_list}"
            )

    async def every_sunday(self, channel_id):
        """
        Run this task every {session_day}.
        """
        channel = await self.bot.fetch_channel(channel_id)
        await channel.send(
            f"Game tonight @ 7:30pm. Please use either `{self.bot.command_prefix}rsvp accept` or `{self.bot.command_prefix}rsvp decline`."
        )

    async def session_decision(self, channel_id, tracker):
        """
        Post a warning that we do not have enough players
        for a full session. Ask for alternative plans.
        """
        channel = await self.bot.fetch_channel(channel_id)
        if (
            len(tracker.rsvp_accept_session_list) < 4
            or len(tracker.rsvp_decline_session_list) > 0
        ):
            await channel.send(
                f"Looks like we don't have all the Bardcore Ruffians available for tonight's session. \n\nWould the group like to have a dream session or cancel? Please use either `{self.bot.command_prefix}vote dream` or `{self.bot.command_prefix}vote cancel`."
            )
