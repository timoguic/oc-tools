import concurrent.futures
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from io import StringIO
from queue import Queue
from threading import Event, Thread

from lxml import etree

from .connector import OcConnector
from .constants import API_BASE_URL, STUDENT_URL
from .session import SessionManager
from .student import Student

logger = logging.getLogger(__name__)


class OcAdapter:
    def __init__(self, username, password):
        self.connector = OcConnector(username, password)

    def _get_sessions(self, before):
        api_url = f"{API_BASE_URL}/users/{self.connector.user_id}/sessions"
        params = {"actor": "expert", "before": before.strftime('%Y-%m-%dT%H:%M:%SZ')}

        data = self.connector.get(api_url, params=params).json()

        return data

    def get_sessions_for_month(self, month):
        now = datetime.now()

        if not month:
            month = datetime.now().month

        after = datetime(now.year, month, 1, 0, 0)
        before = after + timedelta(32)

        manager = SessionManager()
        self.done = Event()
        student_queue = Queue()
        session_thread = Thread(
            target=self._get_sessions_between,
            args=(before, after, student_queue, manager),
            name="sessions",
        )

        logger.info("Starting thread for sessions...")
        session_thread.start()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=5, thread_name_prefix='students'
        ) as executor:
            logger.info("Starting thread pool for students...")
            while not self.done.is_set() or not student_queue.empty():
                student = student_queue.get()
                executor.submit(student.update_financed_status, self.connector)

        session_thread.join()
        logger.info("Sessions thread terminated.")

        return manager

    def _get_sessions_between(self, before, after, queue, manager):
        """Gets the sessions, and posts to the queue

        Meant to be used in a thread. The queue is filled up with students that
        need updating (financed status)
        """
        while before > after:
            sessions = self._get_sessions(before)
            for session in sessions:
                # We remove the +0000 at the end of the date
                session_date = datetime.fromisoformat(session['sessionDate'][:-5])
                before = min(before, session_date)

                if session_date.month == after.month:
                    student_id = session['recipient']['id']

                    student = Student.get_by_id(student_id)
                    if not student:
                        student_name = session['recipient']['displayableName']
                        student = Student(student_id, student_name)
                        # Hopefully the other thread will pick it up :)
                        queue.put(student)

                    level = int(session['projectLevel'])
                    status = session['status']
                    soutenance = session['type'] == "presentation"
                    manager.add(session_date, level, status, soutenance, student)

        self.done.set()
        return manager
