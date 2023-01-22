from discord import Member
from pymongo.results import UpdateResult

from helpers import Collections


class Tracker:
    def __init__(self, db):
        self.attendees = db[Collections.ATTENDEES]
        self.decliners = db[Collections.DECLINERS]
        self.cancellers = db[Collections.CANCELLERS]
        self.inventories = db[Collections.INVENTORIES]
        self.config = db[Collections.CONFIG]
        self.players = db[Collections.PLAYERS]
        self.cancel_flag = db[Collections.CANCEL_SESSION]

    @staticmethod
    def _get_user(user):
        return {"name": user.name, "id": user.id}

    def get_all(self, guild_id):
        attendees = self.get_attendees_for_guild(guild_id)
        decliners = self.get_decliners_for_guild(guild_id)
        cancellers = self.get_cancellers_for_guild(guild_id)
        return attendees, decliners, cancellers

    def get_attendees_for_guild(self, guild_id):
        try:
            return self.attendees.find_one(
                {"guild": guild_id}, {Collections.ATTENDEES: 1, "_id": 0}
            )[Collections.ATTENDEES]
        except TypeError:
            return []

    def get_decliners_for_guild(self, guild_id):
        try:
            return self.decliners.find_one(
                {"guild": guild_id}, {Collections.DECLINERS: 1, "_id": 0}
            )[Collections.DECLINERS]
        except TypeError:
            return []

    def get_cancellers_for_guild(self, guild_id):
        try:
            return self.cancellers.find_one(
                {"guild": guild_id}, {Collections.CANCELLERS: 1, "_id": 0}
            )[Collections.CANCELLERS]
        except TypeError:
            return []

    def get_config_for_guild(self, guild_id):
        try:
            return self.config.find_one(
                {"guild": guild_id}, {Collections.CONFIG: 1, "_id": 0}
            )[Collections.CONFIG]
        except TypeError:
            return None

    def get_players_for_guild(self, guild_id):
        try:
            return self.players.find_one(
                {"guild": guild_id}, {Collections.PLAYERS: 1, "_id": 0}
            )[Collections.PLAYERS]
        except TypeError:
            return None

    def get_dm(self, guild_id):
        try:
            guild_config: dict = self.get_config_for_guild(guild_id)
            return guild_config["session-dm"]["id"]
        except Exception:
            return None

    def get_session_cancel_flag(self, guild_id: int):
        try:
            res = self.config.find_one(
                {"guild": guild_id}, {Collections.CONFIG: 1, "_id": 0}
            )[Collections.CONFIG]
            res = res[Collections.CANCEL_SESSION]
            return res
        except Exception as e:
            return None

    def reset(self, guild_id):
        query = {"guild": guild_id}
        self.attendees.delete_one(query)
        self.decliners.delete_one(query)
        self.cancellers.delete_one(query)
        self.reset_cancel_flag(guild_id)

    def skip(self, guild_id):
        query = {"guild": guild_id}
        self.db.config.update_one({query}, {"config.alerts": False})

    def cancel_session(self, guild_id: int) -> bool:
        guild_config = self.get_config_for_guild(guild_id)
        guild_config.update({Collections.CANCEL_SESSION: True})
        res: UpdateResult = self.config.update_one(
            {"guild": guild_id},
            {
                "$set": {
                    "config": guild_config
                }
            },
            upsert=True
        )
        return True if res.acknowledged else False

    def reset_cancel_flag(self, guild_id: int) -> bool:
        res = self.config.update_one(
            {"guild": guild_id},
            {
                "$set": {
                    "config": {Collections.CANCEL_SESSION: False}
                }
            },
            upsert=True
        )

        return True if res.acknowledged else False

    def add_attendee_for_guild(self, guild_id, attendee):
        return self.attendees.update_one(
            {"guild": guild_id},
            {"$addToSet": {"attendees": self._get_user(attendee)}},
            upsert=True,
        )

    def rm_attendee_for_guild(self, guild_id, attendee):
        return self.attendees.update_one(
            {"guild": guild_id}, {"$pull": {"attendees": self._get_user(attendee)}}
        )

    def add_decliner_for_guild(self, guild_id, decliner):
        return self.decliners.update_one(
            {"guild": guild_id},
            {"$addToSet": {"decliners": self._get_user(decliner)}},
            upsert=True,
        )

    def rm_decliner_for_guild(self, guild_id, decliner):
        return self.decliners.update_one(
            {"guild": guild_id}, {"$pull": {"decliners": self._get_user(decliner)}}
        )

    def add_canceller_for_guild(self, guild_id, canceller):
        return self.cancellers.update_one(
            {"guild": guild_id},
            {"$addToSet": {"cancellers": self._get_user(canceller)}},
            upsert=True,
        )

    def rm_canceller_for_guild(self, guild_id, canceller):
        return self.cancellers.update_one(
            {"guild": guild_id}, {"$pull": {"cancellers": self._get_user(canceller)}}
        )

    def add_player_for_guild(self, guild_id, player):
        return self.players.update_one(
            {"guild": guild_id},
            {"$addToSet": {"players": self._get_user(player)}},
            upsert=True,
        )

    def rm_player_for_guild(self, guild_id, player):
        return self.players.update_one(
            {"guild": guild_id}, {"$pull": {"players": self._get_user(player)}}
        )

    def create_guild_config(
            self,
            guild_id: int,
            vc_id: int,
            dm_user: Member,
            session_day: str,
            session_time: str,
            meeting_room: int,
            first_alert: str,
            second_alert: str,
            cancel_session: bool = False
    ):
        return self.config.update_one(
            {"guild": guild_id},
            {
                "$set": {
                    "guild": guild_id,
                    "config": {
                        "session-dm": self._get_user(dm_user),
                        "vc-id": vc_id,
                        "session-day": session_day,
                        "session-time": str(session_time),
                        "meeting-room": meeting_room,
                        "first-alert": first_alert,
                        "second-alert": second_alert,
                        "alerts": True,
                        "cancel-session": cancel_session
                    },
                }
            },
            upsert=True,
        )

    def rm_guild_config(self, guild_id):
        query = {"guild": guild_id}
        return self.config.delete_one(query)

    def get_first_alert_configs(self, day_of_the_week: int):
        return self.config.find(
            {"config.first-alert": day_of_the_week, "config.alerts": True}
        )

    def get_second_alert_configs(self, day_of_the_week: int):
        return self.config.find(
            {"config.second-alert": day_of_the_week, "config.alerts": True}
        )

    def get_session_day_configs(self, day_of_the_week: int):
        return self.config.find(
            {"config.session-day": day_of_the_week, "config.alerts": True}
        )

    def get_voice_channel_id(self, guild_id: int) -> int:
        res = self.config.find_one({"guild": guild_id})
        sess_config = res["config"]
        return int(sess_config["vc-id"])

    def get_campaign_session_dt(self, guild_id: int) -> tuple[str, str]:
        res = self.config.find_one({"guild": guild_id})
        sess_config = res["config"]
        return sess_config["session-day"], sess_config["session-time"]

    def register_player(self, guild_id: int, player):
        return self.players.update_one(
            {"guild": guild_id},
            {"$addToSet": {Collections.PLAYERS: self._get_user(player)}},
            upsert=True,
        )

    def unregister_player(self, guild_id: int, player):
        return self.players.update_one(
            {"guild": guild_id},
            {"$pull": {Collections.PLAYERS: self._get_user(player)}},
        )

    def is_full_group(self, guild_id: int) -> bool:
        # Check if all the players are registered as attendees
        players = sorted([player["id"] for player in self.get_players_for_guild(guild_id)])
        attendees = sorted([att["id"] for att in self.get_attendees_for_guild(guild_id)])

        # check if attendees contains all elements of players
        return all(elem in attendees for elem in players)

    def is_registered_player(self, guild_id: int, player) -> bool:
        players = self.get_players_for_guild(guild_id)
        return self._get_user(player) in players

    def is_player_dm(self, guild_id: int, player_id: int) -> bool:
        guild_dm_id = self.get_dm(guild_id)
        return True if player_id == guild_dm_id else False

    def is_session_cancelled(self, guild_id: int) -> bool:
        return self.get_session_cancel_flag(guild_id)

    def get_unanswered_players(self, guild_id: int):
        players = {player["id"]: player["name"] for player in self.get_players_for_guild(guild_id)}
        attendees = {att["id"]: att["name"] for att in self.get_attendees_for_guild(guild_id)}
        rejections = {rejecter["id"]: rejecter["name"] for rejecter in self.get_attendees_for_guild(guild_id)}

        # Players: {'a', 'b', 'c', 'd'} | Attendees: {'b', 'd'} | Rejections: {'c'}
        # set_players - set_attendees - set_rejections =
        # Result: {'a'}
        # Return the difference of two or more sets as a new set. (i.e. all elements that are in this set but not the others.)
        unanswered_players = set(players.keys()) - set(attendees.keys()) - set(rejections.keys())

        # Convert set into a list to make it easier to operate with
        unanswered_players = list(unanswered_players)
        if len(unanswered_players) == len(players):
            unanswered_players = ["dnd-players"]
        return unanswered_players
