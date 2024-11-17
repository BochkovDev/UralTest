import json
import inspect
import logging
from functools import wraps

from django.db import connection
from django.test.utils import CaptureQueriesContext


def log_db_queries(func):
    """
    Декоратор для логирования всех запросов к базе данных.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        connection.queries.clear()

        func_name = func.__name__
        func_module = inspect.getmodule(func).__name__
        func_file = inspect.getfile(func)
        func_line = inspect.currentframe().f_lineno

        with CaptureQueriesContext(connection) as queries:
            result = func(*args, **kwargs)

        log_data = {
            "executed_queries": len(queries),
            "function": {
                "name": func_name,
                "module": func_module,
                "file": func_file,
                "line": func_line
            },
            "queries": [
                {
                    "sql": query['sql'].replace('\\"', '"'),
                    "time": query['time'],
                }
                for query in queries
            ]
        }

        pretty_log_data = json.dumps(log_data, indent=4, ensure_ascii=False)
        print(f'\n{pretty_log_data}')

        return result
    return wrapper