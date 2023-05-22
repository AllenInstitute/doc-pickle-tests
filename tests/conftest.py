import pytest
import glob

from . import resolve_env_var, load_pickle


pickle_search_pattern = resolve_env_var("PICKLE_SEARCH_PATTERN")
pickles = glob.glob(pickle_search_pattern)


@pytest.fixture(scope="session", params=pickles)
def raw(request):
    return load_pickle(request.param)
