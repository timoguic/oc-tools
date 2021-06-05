import operator
from dataclasses import dataclass
from datetime import datetime

from .student import Student


@dataclass
class Session:
    """An OC session, with a date, level, status, and student"""

    session_date: datetime
    level: int
    status: str
    student: Student

    @property
    def price(self):
        """Compute the price based on the session details

        Level 1 = 30, level 2 = 35, level 3 = 40
        no show = /2
        auto financé = /2
        everything else... = 0
        """
        price = 25 + 5 * self.level

        if not self.student.financed:
            price = price / 2

        if "absent" in self.status:
            price = price / 2
        elif "completed" not in self.status:
            price = 0

        return price

    def __lt__(self, other):
        if type(other) is not type(self):
            raise TypeError("Invalid type")

        return self.session_date < other.session_date

    def __str__(self):
        return f"{self.student.name: <30} | {self.session_date:%Y-%m-%d %H:%M} | {self.level} | {self.status}"


class SessionManager:
    """This manager makes it easier to filter/search for sessions"""

    def __init__(self):
        self.sessions = list()

    @property
    def month(self):
        return self.sessions[0].session_date.month

    def filter(self, level=None, financed=None, noshow=None, no_charge=None):
        sessions = self.sessions
        if level:
            sessions = [s for s in sessions if s.level == level]

        if financed is not None:
            sessions = [s for s in sessions if s.student.financed is financed]

        if noshow is True:
            sessions = [s for s in sessions if "absent" in s.status]
        elif noshow is False:
            sessions = [s for s in sessions if s.status == "completed"]

        if no_charge is True:
            sessions = [s for s in sessions if s.price == 0]

        return sessions

    def add(self, *args, **kwargs):
        """Add a session to the list, and keep the list sorted"""
        session = Session(*args, **kwargs)
        self.sessions.append(session)
        self.sessions.sort(key=operator.attrgetter("session_date"))
