import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(override=True)

# Load variables from .env.override with higher priority
load_dotenv(dotenv_path=find_dotenv(".env.override"), override=True)


class EnvironmentVariableGetter:
    @staticmethod
    def get(name_of_variable: str) -> str:
        value = os.environ[name_of_variable]
        if value == "":
            raise KeyError(f'The environment variable "{name_of_variable}" is not set!')
        return value
