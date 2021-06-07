import logging
from io import StringIO

from lxml import etree

from .constants import STUDENT_URL

logger = logging.getLogger(__name__)


class Student:
    """Holds information about students

    Additionally, it keeps all students in a class variable dictionary (indexed by student ID)
    """

    _students = dict()

    def __init__(self, student_id, name):
        self.student_id = student_id
        self.name = name
        self.financed = None
        self._students[student_id] = self

    @classmethod
    def get_by_id(cls, student_id):
        return cls._students.get(student_id)

    def update_financed_status(self, connector):
        """Loads the student dashboard and updates their financed status

        Meant to be run in thread / thread pool
        """
        student_url = STUDENT_URL.format(self.student_id)

        resp = connector.get(student_url)

        tree = etree.parse(StringIO(resp.text), etree.HTMLParser())

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

    def __str__(self):
        if type(self.financed) is bool:
            status = ("AF", "F")[self.financed]
        else:
            status = "unknown"

        return f"{self.name} ({status})"
