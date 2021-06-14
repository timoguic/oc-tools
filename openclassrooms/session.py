import operator
from dataclasses import dataclass
from datetime import datetime

from .student import Student, StudentManager


@dataclass
class Session:
    """An OC session, with a date, level, status, and student"""

    session_date: datetime
    level: int
    status: str
    soutenance: bool
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

        # Soutenances are all the same price
        if not self.financed and not self.soutenance:
            price = price / 2

        if self.noshow:
            price = price / 2
        elif not self.completed:
            price = 0

        return price

    @property
    def no_charge(self):
        return self.price == 0
    
    @property
    def financed(self):
        return self.student.financed

    @property
    def noshow(self):
        return "absent" in self.status.lower()

    @property
    def completed(self):
        return "completed" in self.status.lower()
    
    @property
    def pending(self):
        return "pending" in self.status.lower()

    def __str__(self):
        return f"{self.student.name: <30} | {self.session_date:%Y-%m-%d %H:%M} | {self.level} | {self.status}"


class SessionManager:
    """This manager makes it easier to filter/search for sessions"""

    def __init__(self, persistent_students):
        self.sessions = list()
        self.student_manager = StudentManager(persistent_students)

    @property
    def month(self):
        return self.sessions[0].session_date.month

    def filter(
        self, level=None, financed=None, noshow=None, no_charge=None, pending=None, soutenance=False
    ):
        sessions = self.sessions
        if level:
            sessions = [s for s in sessions if s.level == level]

        if financed is not None:
            sessions = [s for s in sessions if s.financed is financed]

        if noshow is True:
            sessions = [s for s in sessions if s.noshow]
        elif noshow is False:
            sessions = [s for s in sessions if s.completed]

        if no_charge is True:
            sessions = [s for s in sessions if s.no_charge]

        if pending is True:
            sessions = [s for s in sessions if s.pending]

        if soutenance is True:
            sessions = [s for s in sessions if s.soutenance]
        else:
            sessions = [s for s in sessions if not s.soutenance]

        return sessions

    def add(self, **kwargs):
        """Add a session to the list, and keep the list sorted"""

        session_args = {
            "session_date": kwargs["session_date"],
            "level": kwargs["level"],
            "status": kwargs["status"],
            "soutenance": kwargs["soutenance"],
            "student": kwargs.get("student", None),
        }

        if session_args["student"] is None:
            student_id = kwargs["student_id"]
            name = kwargs["student_name"]
            student = self.student_manager.get_or_create(student_id, name=name)
            session_args["student"] = student

        session = Session(**session_args)
        self.sessions.append(session)
        self.sessions.sort(key=operator.attrgetter("session_date"))

        if session_args["student"].financed is None:
            return session_args["student"]
