# Base URLs
BASE_URL = "https://openclassrooms.com"
CSRF_URL = BASE_URL + "/login_ajax"
TOKEN_URL = BASE_URL + "/login_check"
LOGIN_URL = BASE_URL + "/login"
DASHBOARD_URL = BASE_URL + "/fr/mentorship/dashboard"
STUDENT_URL = BASE_URL + "/fr/mentorship/students/{}/dashboard"

# API URLs
API_BASE_URL = "https://api.openclassrooms.com"
API_ME_URL = API_BASE_URL + "/me"

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

SHORT_WEEKDAYS = [d.lower()[:3] for d in WEEKDAYS]
