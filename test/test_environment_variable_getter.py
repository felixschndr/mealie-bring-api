import pytest

from source.environment_variable_getter import EnvironmentVariableGetter


@pytest.fixture
def env_var_name():
    return "TEST_ENV_VAR"


@pytest.fixture
def env_var_value():
    return "test_value"


def test_get_existing_env_var(monkeypatch, env_var_name, env_var_value):
    monkeypatch.setenv(env_var_name, env_var_value)

    result = EnvironmentVariableGetter.get(env_var_name)

    assert result == env_var_value


def test_get_non_existent_env_var_with_default(monkeypatch, env_var_name):
    monkeypatch.delenv(env_var_name, raising=False)
    default_value = "default_value"

    result = EnvironmentVariableGetter.get(env_var_name, default_value)

    assert result == default_value


def test_get_non_existent_env_var_without_default(monkeypatch, env_var_name):
    monkeypatch.delenv(env_var_name, raising=False)

    with pytest.raises(RuntimeError) as e:
        EnvironmentVariableGetter.get(env_var_name)

    assert f'The environment variable "{env_var_name}" is not set!' in str(e.value)
