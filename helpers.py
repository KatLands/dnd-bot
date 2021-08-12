import re
from enum import Enum
from typing import Tuple, Set


class Key(str, Enum):
    ATTENDEES = "dnd-bot:unlocked:attendees"
    DECLINERS = "dnd-bot:unlocked:decliners"
    DREAMERS = "dnd-bot:unlocked:dreamers"
    CANCELLERS = "dnd-bot:unlocked:cancellers"
    SKIP = "dnd-bot:unlocked:skip"
    INV = "dnd-bot:locked:inv"


# Trackers
class Tracker:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _builder(key: str, guild: int) -> str:
        return f"{key}:{guild}"

    def get_all(self, guild: str) -> Tuple[Set, Set, Set, Set, Set]:
        return (
            self.get_attendees(guild),
            self.get_decliners(guild),
            self.get_dreamers(guild),
            self.get_cancellers(guild),
            self.isSkip(guild),
        )

    def reset(self, guild: str) -> bool:
        matcher = re.compile(f"dnd-bot:unlocked:\w*:{guild}")
        return self.db.delete(
            *[
                self._builder(key.value, guild)
                for key in Key
                if matcher.match(self._builder(key.value, guild))
            ]
        )

    def skip(self, guild: str) -> bool:
        return self.db.set(self._builder(Key.SKIP, guild), "true")

    def isSkip(self, guild: str) -> bool:
        return bool(self.db.get(self._builder(Key.SKIP, guild)))

    def get_attendees(self, guild: str) -> Set:
        return self.db.smembers(self._builder(Key.ATTENDEES, guild))

    def add_attendee(self, guild: int, attendee: str) -> bool:
        return self.db.sadd(self._builder(Key.ATTENDEES, guild), attendee)

    def remove_attendee(self, guild: int, attendee: str) -> bool:
        return self.db.srem(self._builder(Key.ATTENDEES, guild), attendee)

    def add_decliner(self, guild: int, decliner: str) -> bool:
        return self.db.sadd(self._builder(Key.DECLINERS, guild), decliner)

    def get_decliners(self, guild: int) -> Set:
        return self.db.smembers(self._builder(Key.DECLINERS, guild))

    def remove_decliner(self, guild: int, decliner: str) -> bool:
        return self.db.srem(self._builder(Key.DECLINERS, guild), decliner)

    def get_dreamers(self, guild: int) -> Set:
        return self.db.smembers(self._builder(Key.DREAMERS, guild))

    def add_dreamer(self, guild: int, dreamer: str) -> bool:
        return self.db.sadd(self._builder(Key.DREAMERS, guild), dreamer)

    def get_cancellers(self, guild: int) -> Set:
        return self.db.smembers(self._builder(Key.CANCELLERS, guild))

    def add_canceller(self, guild: int, canceller: str) -> bool:
        return self.db.sadd(self._builder(Key.CANCELLERS, guild), canceller)

    def add_inv(self, guild: int, author: int, inv: str) -> bool:
        player_inv = self.inv_builder(guild, author)
        return self.db.sadd(player_inv, inv)

    def remove_inv(self, guild: int, author, inv: str) -> bool:
        player_inv = self.inv_builder(author)
        return self.db.srem(player_inv, inv)

    def get_inv(self, guild: int, user: str) -> Set:
        return self.db.smembers(self.inv_builder(user))

    def inv_builder(self, guild: int, author) -> str:
        return f"{self._builder(Key.INV, guild)}:{author}"
