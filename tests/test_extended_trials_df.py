def test_response_types(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    response_window_lower = response_window[0] * 1000  # convert to seconds
    response_window_upper = response_window[1] * 1000  # convert to seconds
    print(response_window_lower)
    print(response_window_upper)
    for _, row in extended_trials_df.iterrows():
        print(row["trial_type"])
        print(row["response_type"])
        print(row["lick_times"])
        print(row["change_time"])
        print(row)
        break
