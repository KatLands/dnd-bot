import pprint
import datetime

from enum import Enum, unique
from random import randrange
from pymongo import MongoClient


@unique
class Collections(str, Enum):
    ATTENDEES = "attendees"
    DECLINERS = "decliners"
    DREAMERS = "dreamers"
    CANCELLERS = "cancellers"
    INVENTORIES = "inventories"
    CONFIG = "config"
    PLAYERS = "players"


@unique
class Weekdays(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WENDESAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Tracker:
    def __init__(self, db):
        self.attendees = db[Collections.ATTENDEES]
        self.decliners = db[Collections.DECLINERS]
        self.cancellers = db[Collections.CANCELLERS]
        self.dreamers = db[Collections.DREAMERS]
        self.inventories = db[Collections.INVENTORIES]
        self.config = db[Collections.CONFIG]
        self.players = db[Collections.PLAYERS]

    # Getters
    def get_all(self, guild_id):
        attendees = self.get_attendees_for_guild(guild_id)
        decliners = self.get_decliners_for_guild(guild_id)
        cancellers = self.get_cancellers_for_guild(guild_id)
        dreamers = self.get_dreamers_for_guild(guild_id)
        return (attendees, decliners, cancellers, dreamers)

    def get_attendees_for_guild(self, guild_id):
        try:
            return self.attendees.find_one(
                {"guild": guild_id}, {Collections.ATTENDEES: 1, "_id": 0}
            )[Collections.ATTENDEES]
        except TypeError:
            return None

    def get_decliners_for_guild(self, guild_id):
        try:
            return self.decliners.find_one(
                {"guild": guild_id}, {Collections.DECLINERS: 1, "_id": 0}
            )[Collections.DECLINERS]
        except TypeError:
            return None

    def get_cancellers_for_guild(self, guild_id):
        try:
            return self.cancellers.find_one(
                {"guild": guild_id}, {Collections.CANCELLERS: 1, "_id": 0}
            )[Collections.CANCELLERS]
        except TypeError:
            return None

    def get_dreamers_for_guild(self, guild_id):
        try:
            return self.dreamers.find_one(
                {"guild": guild_id}, {Collections.DREAMERS: 1, "_id": 0}
            )[Collections.DREAMERS]
        except TypeError:
            return None

    def get_inventories_for_guild(self, guild_id):
        return self.inventories.find({"guild": guild_id})

    def get_inventory_for_player(self, guild_id, player):
        try:
            return self.inventories.find_one({"guild": guild_id, "player": player})[
                "inv"
            ]
        except TypeError:
            return None

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

    @staticmethod
    def _get_user(user):
        return {"name": user.name, "id": user.id}

    # Add/Remove
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
            {"$addToSet": {"inv": {"item": item, "qty": qty}}},
            upsert=True,
        )

    def rm_from_player_inventory(self, guild_id, player, item):
        return self.inventories.update_one(
            {"guild": guild_id, "player": self._get_user(player)},
            {"$pull": {"inv": {"item": item}}},
        )

    def update_player_inventory(self, guild_id, player, item, qty):
        return self.inventories.update_one(
            {"guild": guild_id, "player": self._get_user(player), "inv.item": item},
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

    def get_first_alert_configs(self, day_of_the_week: int):
        return self.config.find(
            {"config.first-alert": day_of_the_week, "config.alerts": True}
        )

    def get_second_alert_configs(self, day_of_the_week: int):
        return self.config.find(
            {"config.second-alert": day_of_the_week, "config.alerts": True}
        )


if "__main__" in __name__:
    pp = pprint.PrettyPrinter(indent=4)
    gid = 1234567890
    jane = {"name": "jane", "id": 2233}
    tracker = Tracker(MongoClient("localhost", 27017)["dnd-bot"])

    # Add/remove players
    print(f"Players: {tracker.get_players_for_guild(gid)}")
    tracker.add_player_for_guild(gid, jane)
    print("After adding Jane:")
    pp.pprint(tracker.get_players_for_guild(gid))
    tracker.add_player_for_guild(gid, jane)
    print("After trying to duplicate add Jane:")
    pp.pprint(tracker.get_players_for_guild(gid))
    tracker.rm_player_for_guild(gid, jane)
    print("After removing Jane:")
    pp.pprint(tracker.get_players_for_guild(gid))

    # Add/remove attendees
    print("Attendees:")
    pp.pprint(tracker.get_attendees_for_guild(gid))
    tracker.add_attendee_for_guild(gid, jane)
    print("After adding Jane:")
    pp.pprint(tracker.get_attendees_for_guild(gid))
    tracker.rm_attendee_for_guild(gid, jane)
    print("After removing Jane:")
    pp.pprint(tracker.get_attendees_for_guild(gid))

    # Add/remove decliners
    decl = tracker.get_decliners_for_guild(gid)
    print(f"Decliners: {decl}")
    tracker.add_decliner_for_guild(gid, jane)
    print("After adding Jane:")
    pp.pprint(tracker.get_decliners_for_guild(gid))
    tracker.rm_decliner_for_guild(gid, jane)
    print("After removing Jane:")
    pp.pprint(tracker.get_decliners_for_guild(gid))

    # Add/remove dreamers
    dre = tracker.get_dreamers_for_guild(gid)
    print(f"Dreamers: {dre}")
    tracker.add_dreamer_for_guild(gid, jane)
    print("After adding Jane:")
    pp.pprint(tracker.get_dreamers_for_guild(gid))
    tracker.rm_dreamer_for_guild(gid, jane)
    print("After removing Jane:")
    pp.pprint(tracker.get_dreamers_for_guild(gid))

    # Add/remove cancellers
    canx = tracker.get_cancellers_for_guild(gid)
    print(f"Cancellers: {canx}")
    tracker.add_canceller_for_guild(gid, jane)
    print("After adding Jane:")
    pp.pprint(tracker.get_cancellers_for_guild(gid))
    tracker.rm_canceller_for_guild(gid, jane)
    print("After removing Jane:")
    pp.pprint(tracker.get_cancellers_for_guild(gid))

    # Guild configuration
    gconf = tracker.get_config_for_guild(gid)
    print("Guild config:")
    pp.pprint(gconf)

    # Inventories
    # Get all
    print("Guild inventories:")
    for inv in tracker.get_inventories_for_guild(gid):
        pp.pprint(inv)

    # Get specific player inv
    kali = {"name": "kali", "id": 123455}
    print("Kali's inventory:")
    pp.pprint(tracker.get_inventory_for_player(gid, kali))

    # Update existing item quantity
    random_copper_qty = randrange(1, 100)
    print(f"Update copper amount to {random_copper_qty} in Kali's inv:")
    tracker.update_player_inventory(gid, kali, "copper", random_copper_qty)
    pp.pprint(tracker.get_inventory_for_player(gid, kali))

    # Add new item
    print("Add a book to Kali's inv:")
    tracker.add_to_player_inventory(gid, kali, "book", 1)
    pp.pprint(tracker.get_inventory_for_player(gid, kali))

    # Remove item entry
    print("Remove the book from Kali's inv:")
    tracker.rm_from_player_inventory(gid, kali, "book")
    pp.pprint(tracker.get_inventory_for_player(gid, kali))

    # Non-existent inventory
    print("Jane's non-existent inventory:")
    if tracker.get_inventory_for_player(gid, jane) is None:
        print("No inventory for that user.")
    else:
        print("Was not None...")

    # Guild config
    print("Configure Guild")
    t = datetime.datetime.today().time()
    session_day = Weekdays["sunday".upper()]
    first_alert = Weekdays["Friday".upper()]
    second_alert = Weekdays["SaTuRdAy".upper()]
    tracker.create_guild_config(
        12341234, jane, session_day, t, 111222333, first_alert, second_alert
    )
    pp.pprint(tracker.get_config_for_guild(12341234))
    print(f"All guild configs with first-alert set to Friday ({Weekdays.FRIDAY}):")
    for config in tracker.get_first_alert_configs(Weekdays.FRIDAY):
        pp.pprint(config)
