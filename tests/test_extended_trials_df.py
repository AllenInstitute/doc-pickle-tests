def test_response_types(raw, extended_trials_df):
    response_window = raw["items"]["behavior"]["params"]["response_window"]
    print(extended_trials_df.head())
    raise Exception(response_window)
    for trial in raw["items"]["behavior"]["trial_log"]:
        events = trial["events"]
