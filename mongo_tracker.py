from helpers import Collections


class Tracker:
    def __init__(self, db):
        self.attendees = db[Collections.ATTENDEES]
        self.decliners = db[Collections.DECLINERS]
        self.cancellers = db[Collections.CANCELLERS]
        self.dreamers = db[Collections.DREAMERS]
        self.inventories = db[Collections.INVENTORIES]
        self.config = db[Collections.CONFIG]
        self.players = db[Collections.PLAYERS]

    @staticmethod
    def _get_user(user):
        return {"name": user.name, "id": user.id}

    def get_all(self, guild_id):
        attendees = self.get_attendees_for_guild(guild_id)
        decliners = self.get_decliners_for_guild(guild_id)
        dreamers = self.get_dreamers_for_guild(guild_id)
        cancellers = self.get_cancellers_for_guild(guild_id)
        return (attendees, decliners, dreamers, cancellers)

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

    def get_dreamers_for_guild(self, guild_id):
        try:
            return self.dreamers.find_one(
                {"guild": guild_id}, {Collections.DREAMERS: 1, "_id": 0}
            )[Collections.DREAMERS]
        except TypeError:
            return []

    def get_inventories_for_guild(self, guild_id):
        return self.inventories.find({"guild": guild_id})

    def get_inventory_for_player(self, guild_id, player):
        try:
            return self.inventories.find_one(
                {"guild": guild_id, "player": self._get_user(player)}
            )["inv"]
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
        pass

    def reset(self, guild_id):
        query = {"guild": guild_id}
        self.attendees.delete_one(query)
        self.decliners.delete_one(query)
        self.cancellers.delete_one(query)
        self.dreamers.delete_one(query)

    def skip(self, guild_id):
        query = {"guild": guild_id}
        self.db.config.update_one({query}, {"config.alerts": False})

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

    def add_dreamer_for_guild(self, guild_id, dreamer):
        return self.dreamers.update_one(
            {"guild": guild_id},
            {"$addToSet": {"dreamers": self._get_user(dreamer)}},
            upsert=True,
        )

    def rm_dreamer_for_guild(self, guild_id, dreamer):
        return self.dreamers.update_one(
            {"guild": guild_id}, {"$pull": {"dreamers": self._get_user(dreamer)}}
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

    def add_to_player_inventory(self, guild_id, player, item, qty):
        return self.inventories.update_one(
            {"guild": guild_id, "player": self._get_user(player)},
            {"$addToSet": {"inv": {"item": item.strip(), "qty": qty}}},
            upsert=True,
        )

    def rm_from_player_inventory(self, guild_id, player, item):
        return self.inventories.update_one(
            {"guild": guild_id, "player": self._get_user(player)},
            {"$pull": {"inv": {"item": item}}},
        )

    def update_player_inventory(self, guild_id, player, item, qty):
        return self.inventories.update_one(
            {
                "guild": guild_id,
                "player": self._get_user(player),
                "inv.item": item.strip(),
            },
            {"$set": {"inv.$.qty": qty}},
        )

    def create_guild_config(
            self,
            guild_id,
            dm_user,
            session_day,
            session_time,
            meeting_room,
            first_alert,
            second_alert,
    ):
        return self.config.update_one(
            {"guild": guild_id},
            {
                "$set": {
                    "guild": guild_id,
                    "config": {
                        "session-dm": self._get_user(dm_user),
                        "session-day": session_day,
                        "session-time": str(session_time),
                        "meeting-room": meeting_room,
                        "first-alert": first_alert,
                        "second-alert": second_alert,
                        "alerts": True,
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

    def is_registered_player(self, guild_id: int, player):
        players = self.get_players_for_guild(guild_id)
        return self._get_user(player) in players

    def get_unanswered_players(self, guild_id: int):
        players = {player["id"]: player["name"] for player in self.get_players_for_guild(guild_id)}
        attendees = {att["id"]: att["name"] for att in self.get_attendees_for_guild(guild_id)}
        # Players: a, b, c, d | Attendees: d, b
        # Result: a, c
        # Return the difference of two or more sets as a new set. (i.e. all elements that are in this set but not the others.)
        unanswered_players = list(set(players.keys()).difference(attendees.keys()))
        if len(unanswered_players) == len(players):
            unanswered_players = ["dnd-players"]
        return unanswered_players