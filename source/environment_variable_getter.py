import os
from typing import Any

from dotenv import find_dotenv, load_dotenv

load_dotenv(override=True)

# Load variables from .env.override with higher priority
load_dotenv(dotenv_path=find_dotenv(".env.override"), override=True)


class EnvironmentVariableGetter:
    @staticmethod
    def get(name_of_variable: str, default_value: Any = None) -> str:
        try:
            value = os.environ[name_of_variable]
            if value == "":
                raise KeyError()
            return value
        except KeyError:
            if default_value is not None:
                return default_value

            raise RuntimeError(
                f'The environment variable "{name_of_variable}" is not set!'
            ) from None
