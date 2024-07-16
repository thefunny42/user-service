from functools import wraps

from prometheus_client import Counter


def metrics(name: str, title: str, prefix="userservice"):
    success_counter = Counter(f"{prefix}_{name}", f"{title}")
    failure_counter = Counter(f"{prefix}_{name}_failures", f"{title} failures")

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
            except Exception as error:
                failure_counter.inc()
                raise error
            else:
                success_counter.inc()
                return result

        return wrapper

    return decorator
