import concurrent.futures
import logging
from datetime import datetime, timedelta, timezone
from queue import Queue
from threading import Event, Thread

import dateutil.parser

from .connector import OcConnector
from .constants import API_BASE_URL
from .session import SessionManager

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


class OcAdapter:
    def __init__(self, username, password, persistent_students=False):
        self.connector = OcConnector(username, password)
        self.manager = SessionManager(persistent_students)

    def _get_sessions(self, params=None):
        if params is None:
            params = {}

        # Default value
        params["actor"] = "expert"

        if not params.get("life-cycle-status"):
            params["life-cycle-status"] = ",".join(
                [
                    "canceled",
                    "completed",
                    "late canceled",
                    "marked student as absent",
                    "pending",
                ]
            )

        # Add a before date if we don't have one
        if not params.get("before"):
            params["before"] = _now()

        # Convert the date to the API format
        params["before"] = params["before"].strftime("%Y-%m-%dT%H:%M:%SZ")

        sessions_url = f"{API_BASE_URL}/users/{self.connector.user_id}/sessions"
        data = self.connector.get(sessions_url, params=params).json()
        return data

    def get_sessions_for_month(self, month):
        now = _now()

        if not month:
            month = now.month

        after = datetime(now.year, month, 1, 0, 0, tzinfo=timezone.utc)
        before = after + timedelta(32)

        self.done = Event()
        student_queue = Queue()
        session_thread = Thread(
            target=self._get_sessions_between,
            args=(before, after, student_queue, self.manager),
            name="sessions",
        )

        logger.info("Starting thread for sessions...")
        session_thread.start()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=5, thread_name_prefix="students"
        ) as executor:
            logger.info("Starting thread pool for students...")
            while not self.done.is_set():
                if not student_queue.empty():
                    student = student_queue.get()
                    executor.submit(student.update_financed_status, self.connector)

        session_thread.join()
        logger.info("Sessions thread terminated.")

        self.manager.student_manager.save()

    def _process_session(self, session):
        """Take the JSON session information and returns a dictionary"""

        project_level = session["projectLevel"]
        project_level = int(session["projectLevel"]) if project_level is not None else 0

        return {
            "session_id": session["id"],
            # We remove the +0000 at the end of the date
            "session_date": dateutil.parser.parse(session["sessionDate"]),
            "student_id": session["recipient"]["id"],
            "student_name": session["recipient"]["displayableName"],
            "level": project_level,
            "status": session["status"],
            "soutenance": session["type"] == "presentation",
        }

    def _get_sessions_between(self, before, after, queue, manager):
        """Gets the sessions, and posts to the queue

        Meant to be used in a thread. The queue is filled up with students that
        need updating (financed status)
        """

        while before > after:
            sessions = self._get_sessions(params={"before": before})
            for session in sessions:
                data = self._process_session(session)
                session_date = data["session_date"]
                before = min(before, session_date)

                if session_date.month == after.month and session_date <= _now():
                    # Add the session to the manager
                    student = manager.add(**data)
                    # If the student is not "updated", add it to the queue for updating
                    if student is not None:
                        queue.put(student)

        self.done.set()
        return manager
