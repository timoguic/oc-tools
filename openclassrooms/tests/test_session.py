from datetime import datetime

import pytest

from openclassrooms.session import Session, SessionManager
from openclassrooms.student import Student


@pytest.fixture
def session_manager():
    financed = Student(123, "Financed")
    financed.financed = True
    autof = Student(456, "autof")
    autof.financed = False

    sm = SessionManager()

    sm.add(datetime(2021, 6, 1, 1, 0), 1, "completed", False, financed)
    sm.add(datetime(2021, 6, 2, 1, 0), 2, "canceled", False, financed)
    sm.add(datetime(2021, 6, 3, 1, 0), 2, "completed", False, autof)
    sm.add(datetime(2021, 6, 4, 1, 0), 3, "marked as absent", False, financed)
    sm.add(datetime(2021, 6, 5, 1, 0), 2, "completed", True, financed)
    sm.add(datetime(2021, 6, 6, 1, 0), 3, "completed", True, autof)

    return sm


def test_session_price():
    student = Student(12345, "Test")
    student.financed = True

    session = Session(
        datetime.now(), level=1, status="completed", soutenance=False, student=student
    )

    assert session.price == 30

    session.level = 2
    assert session.price == 35

    session.level = 3
    assert session.price == 40

    student.financed = False
    assert session.price == 20

    session.soutenance = True
    assert session.price == 40

    session.status = "marked as absent"
    assert session.price == 20

    session.status = "canceled"
    assert session.price == 0


def test_session_manager(session_manager):
    assert session_manager.month == 6


def test_session_manager_filter(session_manager):
    assert len(session_manager.filter(level=2)) == 2
    assert len(session_manager.filter(soutenance=True)) == 2
    assert len(session_manager.filter(soutenance=True, level=3)) == 1
    assert len(session_manager.filter(financed=True)) == 3
    assert len(session_manager.filter(noshow=True)) == 1
    assert (
        len(
            session_manager.filter(
                noshow=False, level=3, financed=False, soutenance=True
            )
        )
        == 1
    )
    assert len(session_manager.filter(no_charge=True)) == 1
