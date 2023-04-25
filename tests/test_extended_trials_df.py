import numpy as np


def has_early_response(change_time, lick_times):
    return len(list(filter(lambda value: value < change_time, lick_times))) > 0


def has_response_within_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    response_window_upper = change_time + response_window[1]
    return len(list(filter(lambda value: value >= response_window_lower and value <= response_window_upper, lick_times))) > 0


# def filter_trial_type(trials_df, target_trial_type):
#     return filter(
#         lambda row: row["trial_type"] == target_trial_type,
#         trials_df,
#     )


def test_aborted_trials_early_responses(raw, extended_trials_df):
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "aborted":
            # change_time is nan if change never occurred
            if not np.isnan(change_time) and \
                    not has_early_response(change_time, lick_times):
                bad_trial_indices.append(idx)

    assert len(bad_trial_indices) < 1, \
        f"Aborted trials dont have an early response. Indices: {bad_trial_indices}"


def test_aborted_trials_response_types(raw, extended_trials_df):
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        response_type = row["response_type"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "aborted" and response_type != "EARLY_RESPONSE":
            bad_trial_indices.append(idx)

    assert len(bad_trial_indices) < 1, \
        f"Aborted trials dont have response_type: EARLY_RESPONSE. Indices: {bad_trial_indices}"


def test_go_trials_early_responses(raw, extended_trials_df):
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue
        # if not np.isnan(change_time)
        if trial_type == "go" and has_early_response(change_time, lick_times):
            bad_trial_indices.append(idx)

    assert len(bad_trial_indices) < 1,\
        f"Non-aborted go trials have an early response. Indices: {bad_trial_indices}"


def test_go_trials_response_type(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        response_type = row["response_type"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "go" and \
                response_type == "HIT" and \
                not has_response_within_window(change_time, lick_times, response_window):
            bad_trial_indices.append(idx)

    assert len(bad_trial_indices) < 1, \
        f"Non-aborted go trial has response_type == 'HIT' but doesnt have response within window. trial index: {idx}"


def test_catch_trials_early_response(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        response_type = row["response_type"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "catch":
            assert not has_early_response(change_time, lick_times), \
                f"Non-aborted catch trial has early response. trial index: {idx}"
            if response_type == "FA":
                assert has_response_within_window(change_time, lick_times, response_window), \
                    f"Non-aborted catch trial with response within window not marked as false alarm. trial index: {idx}"


def test_catch_trial_response_type(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    bad_trial_indices = []
    for idx, row in extended_trials_df.iterrows():
        raw_log = raw["items"]["behavior"]["trial_log"][idx]
        trial_type = row["trial_type"]
        change_time = row["change_time"]
        lick_times = row["lick_times"]
        response_type = row["response_type"]
        licks_enabled = raw_log["licks_enabled"]

        if licks_enabled is False:
            # these assertions dont make sense if licks are disabled
            continue

        if trial_type == "catch":
            assert not has_early_response(change_time, lick_times), \
                f"Non-aborted catch trial has early response. trial index: {idx}"
            if response_type == "FA":
                assert has_response_within_window(change_time, lick_times, response_window), \
                    f"Non-aborted catch trial with response within window not marked as false alarm. trial index: {idx}"


# def test_response_types(raw, extended_trials_df):
#     response_window = raw["items"]["behavior"]["params"]["response_window"]
#     bad_trials = []
#     for idx, row in extended_trials_df.iterrows():
#         raw_log = raw["items"]["behavior"]["trial_log"][idx]
#         trial_type = row["trial_type"]
#         change_time = row["change_time"]
#         lick_times = row["lick_times"]
#         response_type = row["response_type"]
#         licks_enabled = raw_log["licks_enabled"]

#         if licks_enabled is False:
#             # these assertions dont make sense if licks are disabled
#             continue

#         trial_summary = {
#             "index": idx,
#             "reason": None,
#         }

#         if trial_type == "aborted":
#             # change_time is nan if change never occurred
#             if not np.isnan(change_time) and \
#                     not has_early_response(change_time, lick_times):
#                 bad_trials.append(
#                     f"Aborted trial doesnt have an early response. Index: {idx}"
#                 )
