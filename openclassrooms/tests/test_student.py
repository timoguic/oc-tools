from unittest.mock import Mock

import pytest

from openclassrooms.student import Student


class MockResponseNoData:
    text = """<html><body></body></html>"""


class MockResponseFinanced:
    text = """<html><body><div class="mentorshipStudent__details oc-typography-body1">
    <p>
    Financé par un tiers
    </p></div></body></html>"""


class MockResponseNotFinanced:
    text = """<html><body><div class="mentorshipStudent__details oc-typography-body1">
    <p>
    Auto-financé
    </p></div></body></html>"""


@pytest.fixture
def connector_no_html():
    connector = Mock()
    connector.get = Mock(return_value=MockResponseNoData())
    return connector


@pytest.fixture
def connector_financed():
    connector = Mock()
    connector.get = Mock(return_value=MockResponseFinanced())
    return connector


@pytest.fixture
def connector_not_financed():
    connector = Mock()
    connector.get = Mock(return_value=MockResponseNotFinanced())
    return connector


def test_student_status_html_missing(connector_no_html):
    no_html = Student(12345, "Error")

    with pytest.raises(RuntimeError):
        no_html.update_financed_status(connector_no_html)


def test_student_status_financed(connector_financed):
    financed = Student(12345, "Financed")
    financed.update_financed_status(connector_financed)
    assert financed.financed is True


def test_student_status_not_financed(connector_not_financed):
    autof = Student(12345, "AutoF")
    autof.update_financed_status(connector_not_financed)
    assert autof.financed is False


def test_student_str():
    no_html = Student(12345, "Error")
    assert str(no_html) == "Error (unknown)"

    no_html.financed = True
    assert str(no_html) == "Error (F)"

    no_html.financed = False
    assert str(no_html) == "Error (AF)"


def test_student_get_by_id():
    no_html = Student(12345, "Error")

    assert Student.get_by_id(12345) == no_html
