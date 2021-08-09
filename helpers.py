from enum import Enum
from typing import Tuple, Set


class Key(str, Enum):
    ATTENDEES = "dnd-bot:attendees"
    DECLINERS = "dnd-bot:decliners"
    DREAMERS = "dnd-bot:dreamers"
    CANCELLERS = "dnd-bot:cancellers"
    SKIP = "dnd-bot:skip"
    INV = "dnd-bot:inv"


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
            self.isSkip(),
        )

    def reset(self) -> bool:
        return self.db.delete(*[key.value for key in Key])

    def skip(self) -> bool:
        return self.db.set(Key.SKIP, "true")

    def isSkip(self) -> bool:
        return bool(self.db.get(Key.SKIP))

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
    
    def add_inv(self, author: int, inv: str) -> bool:
        player_inv = self.inv_builder(author)
        return self.db.sadd(player_inv, inv)

    def remove_inv(self, author, inv: str):
        player_inv = self.inv_builder(author)
        return self.db.srem(player_inv, inv)
    
    def get_inv(self, user: str) -> Set:
        return self.db.smembers(self.inv_builder(user))

    def inv_builder(self, author) -> str:
        return f"{Key.INV}:{author}"

    
