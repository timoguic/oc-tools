# Tools for OpenClassrooms mentors

### Disclaimer: this is a work in progress. Use at your own risk!

### Installation

Python 3.8+ is required.
Install the dependencies with: `pip install -r requirements.txt`.

You can also use the Docker image `timoguic/oc-tools`.

## Authentication

You **MUST** set the values for the environment variables:
* `OC_USERNAME`: your OpenClassrooms username
* `OC_PASSWORD`: your OpenClassrooms password

You can also use an env file (useful for Docker).

## Invoices

Run `python -m openclassrooms.invoice`. It will print the HTML invoice for the current month. Save it into a file, open it in your browser, and enjoy.

If you would like to get the invoice for another month of the same year, use the month number as argument: `python -m openclassrooms.invoice 5` for the month of May (5).

You can also use:
* `--debug`: to display debug information when creating the invoice
* `--text`: to force text format output

Typical usage: `python -m openclassrooms.invoice > report.html` (in a crontab).

## Docker images

### Invoices

Use an env file to store your credentials (see `oc.env`).

Then: `docker run --rm --env-file oc.env timoguic/oc-tools:invoice > report.html`

Build your own: `docker build -f Dockerfile.invoice .`