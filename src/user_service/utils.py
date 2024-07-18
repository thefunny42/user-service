from functools import wraps
from prometheus_client import Counter, make_asgi_app


class Metrics:

    def __init__(self, prefix: str):
        self.prefix = prefix

    @property
    def app(self):
        return make_asgi_app()

    def new(self, name: str, doc: str | None):
        doc = doc or name
        success = Counter(f"{self.prefix}_{name}", f"{doc}")
        failure = Counter(f"{self.prefix}_{name}_failures", f"{doc} failures")
        return (success, failure)

    def measure(self, name: str | None = None, doc: str | None = None):

        def decorator(func):

            success, failure = self.new(
                name=name or func.__name__,
                doc=doc or func.__doc__,
            )

            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                except Exception as error:
                    failure.inc()
                    raise error
                else:
                    success.inc()
                    return result

            return wrapper

        return decorator
