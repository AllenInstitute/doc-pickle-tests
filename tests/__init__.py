from __future__ import annotations

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


def encode_image_name(image_name: str, contrast: int) -> str:
    return f"{image_name}-{contrast}"


def get_initial_image(data: dict) -> str:
    initial_params = data["items"]["behavior"]["params"]["initial_image_params"]
    return encode_image_name(initial_params["Image"], initial_params["contrast"])


# __future__ import not giving me tuple?
Event = typing.Tuple[str, str, float, int]


def filter_events(trial: dict, name_fiter: str) -> list[Event]:
    """Filters event in a trial log entry based on event name.
    """
    return [
        event for event in trial["events"]
        if event[0].startswith(name_fiter)
    ]


# __future__ import not giving me tuple?
Lick = typing.Tuple[float, int]


def is_early_lick(
    lick: Lick,
    response_window_lower: float,
    stimulus_change_events: list[Event],
) -> bool:
    lick_time, _ = lick
    if not lick_time < response_window_lower:
        return False

    # licks dont count as aborts if theyre before the response window but after
    # the stimulus change
    if len(stimulus_change_events) > 0:
        return lick_time < stimulus_change_events[0][2]
    else:
        return True


def classify_licks(trial) -> tuple[list[Lick], list[Lick]]:
    """
    Returns
    -------
    early licks
    licks within window
    """
    response_window_events = filter_events(trial, "response_window")
    if len(response_window_events) < 2:
        abort_events = filter_events(trial, "abort")
        if len(abort_events) < 1:
            raise Exception("No response window but not aborted!")
        return trial["licks"], []

    response_window_lower = response_window_events[0][2]
    response_window_upper = response_window_events[1][2]
    stimulus_change_events = filter_events(trial, "stimulus_changed")
    early = list(filter(
        lambda lick: is_early_lick(
            lick, response_window_lower, stimulus_change_events),
        trial["licks"],
    ))
    within_window = list(filter(
        lambda lick: response_window_lower < lick[0] < response_window_upper,
        trial["licks"],
    ))

    return early, within_window


def filter_trials(behavior_dict: dict, is_catch: False) -> typing.Iterator[dict]:
    """Filters trial log

    Notes
    -----
    - Currently only filters based on if trial is catch or not
    """
    return filter(
        lambda trial: trial["trial_params"]["catch"] == is_catch,
        behavior_dict["items"]["behavior"]["trial_log"],
    )


def lick_within_response_window(lickEvent, response_window_lower: int, response_window_upper: int):
    return lickEvent[3] >= response_window_lower and lickEvent[3] < response_window_upper


def get_invalid_lick_disabled_trials(raw):
    invalid_indices = []
    for log in raw["items"]["behavior"]["trial_log"]:
        if log["licks_enabled"] is True:
            continue

        disabled_licks = filter_events(log, "licks disabled.")
        response_window_events = filter_events(log, "response_window")
        if not len(response_window_events) == 2:
            continue

        within_window_licks = list(filter(
            lambda event: lick_within_response_window(
                event,
                response_window_events[0][3],
                response_window_events[1][3],
            ),
            disabled_licks
        ))

        if not len(within_window_licks) > 0:
            continue

        if len(filter_events(log, "miss")) > 0:
            invalid_indices.append(log["index"])

    return invalid_indices
