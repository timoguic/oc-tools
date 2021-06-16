import json
import logging

from lxml import etree

from .constants import STUDENT_URL

logger = logging.getLogger(__name__)


class Student:
    """Holds information about students"""

    def __init__(self, student_id, name, financed=None):
        self.student_id = student_id
        self.name = name
        self.financed = financed

    def update_financed_status(self, connector):
        """Loads the student dashboard and updates their financed status

        Meant to be run in thread / thread pool
        """
        if self.financed is not None:
            return

        student_url = STUDENT_URL.format(self.student_id)

        resp = connector.get(student_url)

        tree = etree.parse(resp.content, etree.HTMLParser())

        xpath = tree.xpath("//div[contains(@class, 'mentorshipStudent__details')]/p")
        if not len(xpath):
            raise RuntimeError(f"Cannot parse student page: {student_url}")

        status = xpath[0].text.strip()
        if "Auto" in status:
            self.financed = False
        else:
            self.financed = True

        logger.info(f"Updated {self.name} (financed: {self.financed}).")
        return self.financed

    def json(self):
        return {
            "student_id": self.student_id,
            "name": self.name,
            "financed": self.financed,
        }

    def __str__(self):
        if type(self.financed) is bool:
            status = ("AF", "F")[self.financed]
        else:
            status = "unknown"

        return f"{self.name} ({status})"


class StudentManager:
    def __init__(self, persistent=False):
        self.students = {}
        self.persistent = persistent

        if not persistent:
            return

        try:
            with open("students.json", "r") as fp:
                students_dicts = json.load(fp)
        except FileNotFoundError:
            pass

        for student_data in students_dicts:
            self.get_or_create(**student_data)

    def get_or_create(self, student_id, **kwargs):
        student = self.students.get(student_id)

        if student:
            return student

        if not "name" in kwargs:
            return None

        student = Student(student_id, **kwargs)
        self.students[student_id] = student
        self.save()

        return student

    def save(self):
        if not self.persistent:
            return None

        with open("students.json", "w") as fp:
            json.dump([s.json() for s in self.students.values()], fp)
