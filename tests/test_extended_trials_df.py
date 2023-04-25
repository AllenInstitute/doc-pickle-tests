import numpy as np


def has_early_response(change_time, lick_times):
    return len(list(filter(lambda value: value < change_time, lick_times))) > 0


def has_response_within_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    response_window_upper = change_time + response_window[1]
    return len(list(filter(lambda value: value >= response_window_lower and value <= response_window_upper, lick_times))) > 0


def test_trials(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    bad_trials = []
    for idx, row in extended_trials_df.iterrows():
        report = {
            "index": idx,
            "errors": [],
        }
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        licks_enabled = raw_log["licks_enabled"]
        response_type = row["response_type"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "aborted":
            # change_time is nan if change never occurred
            if not np.isnan(change_time) and \
                    not has_early_response(change_time, lick_times):
                report["errors"].append(
                    "Aborted trial doesnt have an early response."
                )
            if response_type != "EARLY_RESPONSE":
                report["errors"].append(
                    "Aborted trial doesnt have response_type: EARLY_RESPONSE."
                )
        elif trial_type == "go":
            if np.isnan(change_time):
                report["errors"].append(
                    "Go trial doesnt have change time."
                )
            else:
                if has_early_response(change_time, lick_times):
                    report["errors"].append(
                        "Non-aborted go trial has early response.")
                if response_type == "HIT" and \
                        not has_response_within_window(change_time, lick_times, response_window):
                    report["errors"].append(
                        "Go trial has response_type == 'HIT' but doesnt have response within window.")
        elif trial_type == "catch":
            if has_early_response(change_time, lick_times):
                report["errors"].append(
                    "Non-aborted catch trial has early response.")
            if response_type == "FA":
                if not has_response_within_window(change_time, lick_times, response_window):
                    report["errors"].append(
                        "Catch trial with response within window not marked as false alarm.")
        else:
            pass

        if len(report["errors"]) > 1:
            bad_trials.append(report)

    assert len(bad_trials) < 1, f"Had bad trials: {bad_trials}"
