from enum import Enum, unique
from typing import List, Tuple


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


@unique
class Emojis(str, Enum):
    MONDAY = "🇲"
    TUESDAY = "🇹"
    WENDESAY = "🇼"
    THURSDAY = "🇷"
    FRIDAY = "🇫"
    SATURDAY = "🇸"
    SUNDAY = "🇺"


def plist(inlist: List) -> str:
    if len(inlist) > 0:
        return ", ".join([u["name"] for u in inlist])
    else:
        return "None"


def adjacent_days(dotw: int) -> Tuple[int, int]:
    if dotw < 0 or dotw > 6:
        raise ValueError
    days = [i for i in range(len(Weekdays))]
    before = days[(dotw - 1) % len(days)]
    after = days[(dotw + 1) % len(days)]
    return (int(before), int(after))


def callable_username(username: str):
    return f"<@{username}>".strip()