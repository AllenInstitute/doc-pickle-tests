import pytest
import glob

from . import load_dotenv, resolve_env_var, load_extended_trials_df, load_pickle


# load_dotenv("./tests/.env")

pickle_search_pattern_var_name = "PICKLE_SEARCH_PATTERN"
pickle_search_pattern = resolve_env_var(pickle_search_pattern_var_name)
pickles = glob.glob(pickle_search_pattern)


@pytest.fixture(scope="session", params=pickles)
def raw(request):
    return load_pickle(request.param)


@pytest.fixture(scope="session")
def extended_trials_df(raw):
    return load_extended_trials_df(raw)
