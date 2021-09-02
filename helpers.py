from typing import List
from enum import Enum, unique


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
