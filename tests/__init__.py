import os
import typing
import pandas as pd
from visual_behavior.translator.core import create_extended_dataframe
from visual_behavior.translator import foraging2


def load_dotenv(path=".env"):
    """load dotenv polyfil
    python-dotenv for 3.7 doesnt seem to be working...>.>!...
    """
    with open(path, "r") as f:
        values = f.readlines()
    for encoded in values:
        name, value = encoded.rstrip().split("=")
        os.environ[name] = value


def resolve_env_var(name: str, required=True) -> typing.Union[str, None]:
    try:
        return os.environ[name]
    except KeyError:
        if required:
            raise Exception(
                "Required environment variable: %s not set." % name)


def load_pickle(path: str) -> typing.Dict:
    return pd.read_pickle(path)


def load_extended_trials_df(raw: typing.Dict) -> pd.DataFrame:
    core_data = foraging2.data_to_change_detection_core(raw)
    return create_extended_dataframe(
        trials=core_data['trials'],
        metadata=core_data['metadata'],
        licks=core_data['licks'],
        time=core_data['time'],
    )
