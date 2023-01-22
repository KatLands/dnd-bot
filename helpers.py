from datetime import datetime, timedelta
from enum import Enum, unique
from typing import List, Tuple

from pytz import timezone

est_tz = timezone("America/New_York")


@unique
class Collections(str, Enum):
    ATTENDEES = "attendees"
    DECLINERS = "decliners"
    CANCELLERS = "cancellers"
    INVENTORIES = "inventories"
    CONFIG = "config"
    PLAYERS = "players"
    CANCEL_SESSION = "cancel-session"


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
    return int(before), int(after)


def get_next_session_day(session_day, session_time) -> datetime:
    # Get current DT and localize it to EST
    est_dt = datetime.utcnow().astimezone(est_tz)

    # Figure out next session date with time deltas
    for i in range(1, 8):
        ret_sess_day = datetime.utcnow().astimezone(est_tz)
        potential_day: datetime = est_dt + timedelta(days=i)
        potential_day_dotw = potential_day.weekday()

        if potential_day_dotw == session_day:
            ret_sess_day = potential_day.replace(
                hour=int(session_time.split(":")[0]),
                minute=int(session_time.split(":")[1]),
            )
        return ret_sess_day


def callable_username(username: str):
    return f"<@{username}>".strip()