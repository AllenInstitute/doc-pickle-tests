from __future__ import annotations

import pytest
import typing

from . import get_initial_image


Lick = typing.Tuple[float, int]
Event = typing.Tuple[str, str, float, int]


def filter_events(trial: dict, name_fiter: str) -> list[Event]:
    return [
        event for event in trial["events"]
        if event[0].startswith(name_fiter)
    ]


def classify_licks(trial) -> tuple[list[Lick], list[Lick]]:
    """
    Returns
    -------
    early licks
    licks within window
    """
    response_window_events = filter_events(trial, "response_window")
    if not len(response_window_events) != 2:
        raise Exception("Unexpected response window length.")

    response_window_lower = response_window_events[0][2]
    response_window_upper = response_window_events[1][2]

    early = list(filter(
        lambda lick: lick[0] < response_window_lower,
        trial["licks"],
    ))
    within_window = list(filter(
        lambda lick: response_window_lower < lick[0] < response_window_upper,
        trial["licks"],
    ))

    return early, within_window


@pytest.fixture
def go_trials(raw):
    return list(filter(
        lambda trial: trial["trial_params"]["catch"] is False,
        raw["items"]["behavior"]["trial_log"]
    ))


@pytest.fixture
def catch_trials(raw):
    return list(filter(
        lambda trial: trial["trial_params"]["catch"] is True,
        raw["items"]["behavior"]["trial_log"]
    ))


# this is wrong...probably
# def test_go_trials_have_changes(raw):
#     bad_trial_indices = []
#     for trial in raw["items"]["behavior"]["trial_log"]:
#         if trial["trial_params"]["catch"] is False and \
#                 len(trial["stimulus_changes"]) > 0:
#             bad_trial_indices.append(trial["index"])

#     assert len(bad_trial_indices) < 1, \
#         f"Go trials dont have stimulus changes. Indices: {bad_trial_indices}"


def test_catch_trials_have_no_changes(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is True and \
                len(trial["stimulus_changes"]) > 1 and \
                trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]:  # catch trials with stimulus changes to different stim is bad
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Catch trials have stimulus changes. Indices: {bad_trial_indices}"

# temp, will fail for converted dynamic routing pickles
# def test_autorewarded_trials_have_changes(raw):
#     bad_trial_indices = []
#     for trial in raw["items"]["behavior"]["trial_log"]:
#         if trial["trial_params"]["auto_reward"] is True and \
#                 len(trial["stimulus_changes"]) > 0:
#             bad_trial_indices.append(trial["index"])

#     assert len(bad_trial_indices) < 1, \
#         f"Autorewarded trials domt have stimulus changes. Indices: {bad_trial_indices}"


def test_image_sequence(raw):
    prev = get_initial_image(raw)
    for trial in raw["items"]["behavior"]["trial_log"]:
        if len(trial["stimulus_changes"]) > 0:
            initial_image = trial["stimulus_changes"][0][0][0]
            change_image = trial["stimulus_changes"][0][1][0]
            assert prev == initial_image, \
                "Initial image for a change should be the change image from the last trial with a stimulus change."
            prev = change_image


def test_go_trials_have_correct_event_log(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is False:
            for event in trial["events"]:
                # these events should not be present
                if event[0] in ["sham_change", "rejection", "false_alarm"]:
                    bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Go trials have coorect event log. Indices: {bad_trial_indices}"


def test_catch_trials_have_correct_event_log(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is True:
            for event in trial["events"]:
                # these events should not be present
                if event[0] in ["change", "miss", "false_alarm"]:
                    bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Catch trials have stimulus changes. Indices: {bad_trial_indices}"


# def test_catch_trials_have_correct_event_log(raw):
#     bad_trial_indices = []
#     for trial in raw["items"]["behavior"]["trial_log"]:
#         if trial["trial_params"]["catch"] is True:
#             for event in trial["events"]:
#                 # these events should not be present
#                 if event[0] in ["change", "miss", "false_alarm", "rejection"]:
#                     bad_trial_indices.append(trial["index"])

# def has_for_abort_and_early_response_event(trial) -> bool:
#     events = list(filter(
#         # gets first item of iterable?
#         lambda event_name, : event_name in ["abort", "early_response"],
#         trial["events"],
#     ))
#     has_abort_event = any(
#         lambda event_name, : event_name == "abort",
#         events
#     )
#     has_early_response_event = any(
#         lambda event_name, : event_name == "early_response",
#         events
#     )

#     return


# def has_early_lick(trial, epoch_start: float, epoch_end: float) -> bool:
#     """
#     Notes
#     -----
#     - This is probably unnecessary?
#     """
#     return any(
#         trial["lick_events"],
#         lambda event: epoch_start < event["wut"] < epoch_end
#     )


# def get_first_lick(trial) -> tuple[float, int] | None:
#     licks = trial["licks"]

#     if len(licks) > 0:
#         return licks[0]


# def calculate_early_lick_window(behavior_dict) -> tuple[float, float]:
#     # this hopefully always exists here?
#     response_window_lower = behavior_dict["items"]["behavior"]["params"]["response_window"][0]


def test_aborts(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        events = list(filter(
            # , gets first item of iterable?
            lambda event_name, : event_name in ["abort", "early_response"],
            trial["events"],
        ))
        has_abort_event = any(
            lambda event_name, : event_name == "abort",
            events
        )
        has_early_response_event = any(
            lambda event_name, : event_name == "early_response",
            events
        )

        # TODO: do this better?
        if has_abort_event and not has_early_response_event:
            bad_trial_indices.append(trial["index"])
        elif not has_abort_event and has_early_response_event:
            bad_trial_indices.append(trial["index"])
        else:
            pass

    assert len(bad_trial_indices) < 1, \
        f"Bad trials. Indices: {bad_trial_indices}"


def test_non_abort_event_log(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        abort_events = filter_events(trial, "abort")
        if len(abort_events) < 1:
            continue

        early, within = classify_licks(trial)
        hit_events = filter_events(trial, "hit")
        miss_events = filter_events(trial, "miss")
        rejection_events = filter_events(trial, "rejection")
        false_alarm_events = filter_events(trial, "false_alarm")
        if trial["trial_params"]["catch"] is False:
            if len(within) > 0:
                if any([
                    len(hit_events) < 1,
                    len(miss_events) > 0,
                    len(rejection_events) > 0,
                    len(false_alarm_events) > 0,
                ]):
                    bad_trial_indices.append(trial["index"])
            elif len(within) < 0:
                if any([
                    len(miss_events) < 1,
                    len(rejection_events) > 0,
                    len(hit_events) > 0,
                    len(false_alarm_events) > 0,
                ]):
                    bad_trial_indices.append(trial["index"])
        elif trial["trial_params"]["catch"] is True:
            if len(within) > 0:
                if any([
                    len(rejection_events) < 1,
                    len(false_alarm_events) > 0,
                    len(hit_events) > 0,
                    len(miss_events) > 0,
                ]):
                    bad_trial_indices.append(trial["index"])
            elif len(within) < 0:
                if any([
                    len(false_alarm_events) < 1,
                    len(hit_events) > 0,
                    len(miss_events) > 0,
                    len(rejection_events) > 0,
                ]):
                    bad_trial_indices.append(trial["index"])
        else:
            raise Exception("Unexpected catch type.")

    assert len(bad_trial_indices) < 1, \
        f"Bad trials. Indices: {bad_trial_indices}"


def test_non_abort_catch_same_image(raw):
    """Tests all non-abort catch trials have same image
    """
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is True:
            stimulus_changes = trial["stimulus_changes"]
            if len(stimulus_changes) > 0 and \
                    stimulus_changes[0][0][0] != stimulus_changes[0][1][0]:
                bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Bad trials. Indices: {bad_trial_indices}"


def test_non_abort_go_have_change(raw):
    """Tests all non-abort go trials have a change
    """
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is False:
            abort_events = filter_events(trial, "abort")
            if len(abort_events) < 1 and len(trial["stimulus_changes"]) > 1:
                bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Bad trials. Indices: {bad_trial_indices}"
