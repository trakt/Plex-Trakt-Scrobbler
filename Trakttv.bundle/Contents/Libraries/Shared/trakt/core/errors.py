ERRORS = {
    400: ("Bad Request",            "Request couldn't be parsed"),
    401: ("Unauthorized",           "OAuth must be provided"),
    403: ("Forbidden",              "Invalid API key or unapproved app"),
    404: ("Not Found",              "Method exists, but no record found"),
    405: ("Method Not Found",       "Method doesn't exist"),
    409: ("Conflict",               "Resource already created"),
    412: ("Precondition Failed",    "Use application/json content type"),
    422: ("Unprocessible Entity",   "Validation error"),
    429: ("Rate Limit Exceeded",    "Rate limit exceeded"),

    500: ("Server Error",           "Server error"),
    502: ("Bad Gateway",            "Server unavailable"),
    503: ("Service Unavailable",    "Server overloaded (try again in 30s)"),
    504: ("Service Unavailable",    "Server overloaded (try again in 30s)"),

    520: ("Service Unavailable",    "CloudFlare: Web server is returning an unknown error"),
    521: ("Service Unavailable",    "CloudFlare: Web server is down"),
    522: ("Service Unavailable",    "CloudFlare: Connection timed out"),
    524: ("Service Unavailable",    "CloudFlare: A timeout occurred")
}
