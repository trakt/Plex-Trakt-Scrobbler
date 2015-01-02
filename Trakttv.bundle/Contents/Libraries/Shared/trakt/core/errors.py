ERRORS = {
    400: ("Bad Request",            "request couldn't be parsed"),
    401: ("Unauthorized",           "OAuth must be provided"),
    403: ("Forbidden",              "invalid API key"),
    404: ("Not Found",              "method exists, but no record found"),
    405: ("Method Not Found",       "method doesn't exist"),
    409: ("Conflict",               "resource already created"),
    422: ("Unprocessable Entity",   "validation errors"),
    429: ("Rate Limit Exceeded",    ""),
    500: ("Server Error",           ""),
    503: ("Service Unavailable",    "server overloaded"),
}
