from . import get_initial_image


def test_go_trials_have_changes(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is False and \
                len(trial["stimulus_changes"]) > 0:
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Go trials dont have stimulus changes. Indices: {bad_trial_indices}"


def test_catch_trials_have_no_changes(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is True and \
                len(trial["stimulus_changes"]) < 1:
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Catch trials have stimulus changes. Indices: {bad_trial_indices}"


def test_autorewarded_trials_have_changes(raw):
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["auto_reward"] is True and \
                len(trial["stimulus_changes"]) > 0:
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Autorewarded trials domt have stimulus changes. Indices: {bad_trial_indices}"


def test_image_sequence(raw):
    prev = get_initial_image(raw)
    for trial in raw["items"]["behavior"]["trial_log"]:
        if len(trial["stimulus_changes"]) > 0:
            initial_image = trial["stimulus_changes"][0][0][0]
            change_image = trial["stimulus_changes"][0][1][0]
            assert prev == initial_image, \
                "Initial image for a change should be the change image from the last trial with a stimulus change."
            prev = change_image
