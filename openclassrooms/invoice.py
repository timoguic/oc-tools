import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .adapter import OcAdapter
from .helpers import get_username_password

class Invoice:
    """Format data to prepare the invoice

    Gets the sessions from the manager, and filters / calculate prices.
    """

    HTML_TEMPLATE = "invoice.html"
    TEXT_TEMPLATE = "invoice.txt"

    def __init__(self, adapter, duration):
        self.manager = adapter.manager
        self.month = adapter.manager.month
        self.duration = duration

    @property
    def data(self):
        data = {
            "month": self.month,
            "sessions": self.filtered_sessions,
            "af_students": self.af_students,
            "no_charge": self.manager.filter(no_charge=True),
            "to_complete": self.manager.filter(pending=True),
            "duration": self.duration,
            "now": datetime.now(),
        }
        return data

    def print(self, html=True):
        print(self.render(html))

    def render(self, html=True):
        env = Environment(
            loader=PackageLoader("openclassrooms"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["round2dec"] = lambda v: f"{v:.2f}"
        env.filters["nice_date"] = lambda v: f"{v:%a %d %b %Y @ %H:%M}"
        template_file = self.HTML_TEMPLATE if html else self.TEXT_TEMPLATE
        tpl = env.get_template(template_file)
        return tpl.render(**self.data)

    @property
    def af_students(self):
        return {sess.student for sess in self.manager.filter(financed=False)}

    @property
    def filtered_sessions(self):
        output = {}

        # OC levels
        for level in (1, 2, 3):
            # auto financé / financé
            for financed in False, True:
                # Some labels to make it easier to read
                label_f = ("AutoF", "F")[financed]
                for noshow in False, True:
                    # No shows
                    label_noshow = ("", "noshow")[noshow]

                    # Generate the filters
                    filters = {
                        "level": level,
                        "financed": financed,
                        "noshow": noshow,
                        "soutenance": False,
                    }
                    label = f"NIVEAU {level} / {label_f} {label_noshow}"
                    sessions = self.manager.filter(**filters)
                    output[label] = sessions

            for noshow in False, True:
                label_noshow = ("", "noshow")[noshow]
                filters = {
                    "level": level,
                    "noshow": noshow,
                    "soutenance": True,
                }
                label = f"SOUTENANCES NIVEAU {level} {label_noshow}"
                sessions = self.manager.filter(**filters)
                output[label] = sessions

        return output


def print_invoice(month=None, html=True):
    username, password = get_username_password()

    start = time.time()
    adapter = OcAdapter(username, password, persistent_students=True)
    adapter.get_sessions_for_month(month)
    end = time.time()

    invoice = Invoice(adapter, end - start)

    invoice.print(html=html)

def demo_invoice(html=True):
    start = time.time()
    import pickle
    with open("manager.dat", "rb") as fp:
        manager = pickle.load(fp)
    end = time.time()

    invoice = Invoice(manager, end - start)

    invoice.print(html=html)


LOG_FORMAT = "%(levelname)s:%(module)s [%(threadName)s]: %(msg)s"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Creates an OC invoice')

    parser.add_argument(
        'month_number', metavar='N', type=int, nargs='?', help='the month number'
    )

    parser.add_argument('--debug', action="store_true")
    parser.add_argument('--text', action="store_true", default=False)
    parser.add_argument('--demo', action="store_true", default=False)

    args = parser.parse_args()

    process_html = not args.text

    if args.demo:
        demo_invoice(not args.text)
        import sys
        sys.exit(0)

    try:
        log_level = logging.WARNING
        if args.debug:
            log_level = logging.INFO

        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        print_invoice(args.month_number, html=process_html)
    except RuntimeError as e:
        print("An error occurred:", e)
