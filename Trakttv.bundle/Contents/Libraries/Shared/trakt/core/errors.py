ERRORS = {
    400: ("Bad Request",            "request couldn't be parsed"),
    401: ("Unauthorized",           "OAuth must be provided"),
    403: ("Forbidden",              "invalid API key"),
    404: ("Not Found",              "method exists, but no record found"),
    405: ("Method Not Found",       "method doesn't exist"),
    409: ("Conflict",               "resource already created"),
    422: ("Unprocessable Entity",   "validation error"),
    429: ("Rate Limit Exceeded",    "rate limit exceeded"),
    500: ("Server Error",           "server error"),
    502: ("Bad Gateway",            "server unavailable"),
    503: ("Service Unavailable",    "server overloaded"),
    504: ("Gateway Timeout",        "server timeout"),
    520: ("Website is offline",     "Web server is returning an unknown error")
}
