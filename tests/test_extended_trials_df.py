def has_response_before_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    return len(list(filter(lambda value: value < response_window_lower, lick_times))) > 0


def has_response_within_window(change_time, lick_times, response_window):
    response_window_lower = change_time + response_window[0]
    response_window_upper = change_time + response_window[1]
    return len(list(filter(lambda value: value >= response_window_lower and value <= response_window_upper, lick_times))) > 0


def test_response_types(raw, extended_trials_df):
    response_window_lower, response_window_upper = raw[
        "items"]["behavior"]["params"]["response_window"]
    print(response_window_lower)
    print(response_window_upper)
    for _, row in extended_trials_df.iterrows():
        print(row["trial_type"])
        print(row["response_type"])
        print(row["lick_times"])
        print(row["change_time"])
        print(row)
        break
    raise Exception("bur")
