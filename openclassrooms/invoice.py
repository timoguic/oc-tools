import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from mako.template import Template

from .adapter import OcAdapter
from .helpers import get_username_password


class Invoice:
    """Format data to prepare the invoice

    Gets the sessions from the manager, and filters / calculate prices.
    """

    def __init__(self, manager, duration):
        self.manager = manager
        self.duration = duration

    def print(self, html=True):
        contents = self.html() if html else self.report()
        print(contents)

    def __str__(self):
        return self.report()

    @staticmethod
    def header(txt):
        return f"\n{'-' * 80}\n{str(txt)}\n"

    @staticmethod
    def indent(txt, level=1):
        return f"{' ' * 2 * level} {str(txt)}\n"

    @staticmethod
    def subtotal(txt, count=None, unique_price=None):
        out = f"-- SUBTOTAL "

        if count is not None:
            out += f"{count} x "

        if unique_price is not None:
            out += f"{unique_price} = "

        out += f"{txt:.2f}\n"
        return out

    def footer(self):
        return f"\n\nGenerated on {datetime.now():%d %b %Y @ %H:%M} in {self.duration:.2f}s"

    def _get_filtered_sessions(self):
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

    def html(self):
        """Generate the HTML 'invoice'"""
        template_path = Path(__file__).parent / "templates" / "invoice.html"
        tpl = Template(filename=str(template_path))
        html = tpl.render(
            month=self.manager.month,
            sessions=self._get_filtered_sessions(),
            af_students={s.student for s in self.manager.filter(financed=False)},
            no_charge=[s for s in self.manager.filter(no_charge=True)],
            duration=self.duration,
        )

        return html

    def report(self):
        """Generate the string output for the 'invoice'"""
        output = ""
        total = 0
        filtered_sessions = self._get_filtered_sessions()
        for label, sessions in filtered_sessions.items():
            # If there are no matching sessions, skip to the next group
            if not len(sessions):
                continue

            # Generate the table with the session list
            output += self.header(label)
            for sess in sessions:
                output += self.indent(sess)

            # Computes subtotal, and writes it
            sublist = [s.price for s in sessions]
            subtotal = sum(sublist)
            output += self.subtotal(
                subtotal, count=len(sublist), unique_price=sessions[0].price
            )
            total += subtotal

        # AF students provide a monthly flat bonus
        af_students = {s.student for s in self.manager.filter(financed=False)}
        output += self.header("AF BONUS")
        for student in af_students:
            output += self.indent(student)

        # Add it to the invoice
        subtotal = 30 * len(af_students)
        output += self.subtotal(subtotal, count=len(af_students), unique_price=30)
        total += subtotal

        output += f"\n== TOTAL = {total:.2f}\n"

        output += self.footer()

        return output


def print_invoice(month=None, html=True):
    username, password = get_username_password()

    start = time.time()
    adapter = OcAdapter(username, password)
    manager = adapter.get_sessions_for_month(month)
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

    args = parser.parse_args()

    process_html = not args.text

    try:
        log_level = logging.WARNING
        if args.debug:
            log_level = logging.INFO

        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        print_invoice(args.month_number, html=process_html)
    except RuntimeError as e:
        print("An error occurred:", e)
