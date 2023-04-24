import numpy as np


def has_early_response(change_time, lick_times):
    return len(list(filter(lambda value: value < change_time, lick_times))) > 0


def has_response_before_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    return len(list(filter(lambda value: value < response_window_lower, lick_times))) > 0


def has_response_within_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    response_window_upper = change_time + response_window[1]
    return len(list(filter(lambda value: value >= response_window_lower and value <= response_window_upper, lick_times))) > 0


# def test_response_types(raw, extended_trials_df):
#     response_window = raw["items"]["behavior"]["params"]["response_window"]
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

#         if trial_type == "aborted":
#             if not np.isnan(change_time):  # change_time is nan if change never occurred
#                 assert has_response_before_window(change_time, lick_times, response_window), \
#                     f"Aborted trial doesnt have early response. trial index: {idx}"
#         elif trial_type == "autorewarded":
#             pass
#         elif trial_type == "go":
#             assert not has_response_before_window(change_time, lick_times, response_window), \
#                 f"Non-aborted go trial has early response. trial index: {idx}"
#             if response_type == "HIT":
#                 assert has_response_within_window(change_time, lick_times, response_window), \
#                     f"Non-aborted go trial has response_type == 'HIT' but doesnt have response within window. trial index: {idx}"
#         elif trial_type == "catch":
#             assert not has_response_before_window(change_time, lick_times, response_window), \
#                 f"Non-aborted catch has early response. trial index: {idx}"
#             if response_type == "FA":
#                 assert has_response_within_window(change_time, lick_times, response_window), \
#                     f"Non-aborted catch trial with response within window not marked as false alarm. trial index: {idx}"
#         else:
#             raise Exception("Unexpected trial_type=%s" % trial_type)


def test_aborted_trials(raw, extended_trials_df):
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

        if trial_type == "aborted":
            if not np.isnan(change_time):  # change_time is nan if change never occurred
                assert has_early_response(change_time, lick_times), \
                    f"Aborted trial doesnt have early response. trial index: {idx}"
            assert response_type == "EARLY_RESPONSE", \
                f"Aborted trial response_type not EARLY_RESPONSE. trial index: {idx}"
