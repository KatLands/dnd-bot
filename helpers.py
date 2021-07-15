from enum import Enum
from typing import Tuple, Set


class Key(str, Enum):
    ATTENDEES = "dnd-bot:attendees"
    DECLINERS = "dnd-bot:decliners"
    DREAMERS = "dnd-bot:dreamers"
    CANCELLERS = "dnd-bot:cancellers"


# Trackers
class Tracker:
    def __init__(self, db):
        self.db = db

    def get_all(self) -> Tuple[Set, Set, Set, Set]:
        return (
            self.get_attendees(),
            self.get_decliners(),
            self.get_dreamers(),
            self.get_cancellers(),
        )

    def reset(self) -> bool:
        return self.db.delete(
            Key.ATTENDEES, Key.DECLINERS, Key.DREAMERS, Key.CANCELLERS
        )

    def get_attendees(self) -> Set:
        return self.db.smembers(Key.ATTENDEES)

    def add_attendee(self, attendee: str) -> bool:
        return self.db.sadd(Key.ATTENDEES, attendee)

    def remove_attendee(self, attendee: str) -> bool:
        return self.db.srem(Key.ATTENDEES, attendee)

    def add_decliner(self, decliner: str) -> bool:
        return self.db.sadd(Key.DECLINERS, decliner)

    def get_decliners(self) -> Set:
        return self.db.smembers(Key.DECLINERS)

    def remove_decliner(self, decliner: str) -> bool:
        return self.db.srem(Key.DECLINERS, decliner)

    def get_dreamers(self) -> Set:
        return self.db.smembers(Key.DREAMERS)

    def add_dreamer(self, dreamer: str) -> bool:
        return self.db.sadd(Key.DREAMERS, dreamer)

    def get_cancellers(self) -> Set:
        return self.db.smembers(Key.CANCELLERS)

    def add_canceller(self, canceller: str) -> bool:
        return self.db.sadd(Key.CANCELLERS, canceller)
