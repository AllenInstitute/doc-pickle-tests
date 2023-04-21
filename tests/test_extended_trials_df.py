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
