# Trackers
class Tracker:
    _ATTENDEES = "attendees"
    _DECLINERS = "decliners"
    _DREAMERS = "dreamers"
    _CANCELLERS = "cancellers"

    def __init__(self, db):
        self.db = db

    @property
    def MEMBERS(self):
        return self._MEMBERS

    @property
    def ATTENDEES(self):
        return self._ATTENDEES

    @property
    def DECLINERS(self):
        return self._DECLINERS

    @property
    def DREAMERS(self):
        return self._DREAMERS

    @property
    def CANCELLERS(self):
        return self._CANCELLERS

    def get_all(self):
        return (
            self.get_attendees(),
            self.get_decliners(),
            self.get_dreamers(),
            self.get_cancellers(),
        )

    def reset(self):
        return self.db.delete(
            self.ATTENDEES, self.DECLINERS, self.DREAMERS, self.CANCELLERS
        )

    def get_attendees(self):
        return self.db.smembers(self.ATTENDEES)

    def add_attendee(self, attendee):
        return self.db.sadd(self.ATTENDEES, attendee)

    def remove_attendee(self, attendee):
        return self.db.srem(self.ATTENDEES, attendee)

    def add_decliner(self, decliner):
        return self.db.sadd(self.DECLINERS, decliner)

    def get_decliners(self):
        return self.db.smembers(self.DECLINERS)

    def remove_decliner(self, decliner):
        return self.db.srem(self.DECLINERS, decliner)

    def get_dreamers(self):
        return self.db.smembers(self.DREAMERS)

    def add_dreamer(self, dreamer):
        return self.db.sadd(self.DREAMERS, dreamer)

    def get_cancellers(self):
        return self.db.smembers(self.CANCELLERS)

    def add_canceller(self, canceller):
        return self.db.sadd(self.CANCELLERS, canceller)
