import pytest
import os
import glob

from . import resolve_env_var, load_extended_trials_df, load_pickle

pickle_dir_var_name = "DOC_PICKLE_DIR"
pickle_dir = resolve_env_var(pickle_dir_var_name)

if not os.path.isdir(pickle_dir):
    raise Exception(
        "%s=%s, doesnt appear to be a directory." %
        (pickle_dir_var_name, pickle_dir, )
    )

pickles = glob.glob(os.path.join(pickle_dir, "*.pkl"))


@pytest.fixture(scope="session", params=pickles)
def raw(request):
    return load_pickle(request)


@pytest.fixture(scope="session")
def extended_trials_df(raw):
    return load_extended_trials_df(raw)
