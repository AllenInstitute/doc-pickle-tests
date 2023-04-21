from . import get_initial_image


# to test loading
# def one(x):
#     assert len(x) == 1
#     if isinstance(x, set):
#         return list(x)[0]
#     else:
#         return x[0]


# def load_behavior_pickle(foraging_file_name):
#     data = pd.read_pickle(foraging_file_name)
#     core_data = foraging2.data_to_change_detection_core(data)

#     df = create_extended_dataframe(
#         trials=core_data['trials'], metadata=core_data['metadata'], licks=core_data['licks'], time=core_data['time'],)

#     behavior_session_uuid = one(df['behavior_session_uuid'].unique())

#     ets = ExtendedTrialSchema()
#     data_list_cs = df.to_dict('records')
#     data_list_cs_sc = ets.dump(data_list_cs, many=True)
#     data_package_cs = json.dumps({'data_list': data_list_cs_sc})
#     return data_package_cs


def test_go_trials_have_changes(raw):
    for trial in raw["items"]["behavior"]["trial_log"]:
        assert trial["trial_params"]["catch"] is False and len(
            trial["stimulus_changes"]) > 0


def test_catch_trials_have_no_changes(raw):
    for trial in raw["items"]["behavior"]["trial_log"]:
        assert trial["trial_params"]["catch"] is True and len(
            trial["stimulus_changes"]) < 1


def test_autorewarded_trials_have_changes(raw):
    for trial in raw["items"]["behavior"]["trial_log"]:
        assert trial["trial_params"]["auto_reward"] is True and len(
            trial["stimulus_changes"]) > 0


def test_image_sequence(raw):
    prev = get_initial_image(raw)
    for trial in raw["items"]["behavior"]["trial_log"]:
        if len(trial["stimulus_changes"]) > 0:
            initial_image = trial["stimulus_changes"][0][0][0]
            change_image = trial["stimulus_changes"][0][1][0]
            assert prev == initial_image, \
                "Initial image for a change should be the change image from the last trial with a stimulus change."
            prev = change_image
