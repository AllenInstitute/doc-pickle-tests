import pytest

from . import get_initial_image, filter_events, filter_trials, classify_licks, resolve_env_var


skip_lick_abort_tests = not bool(resolve_env_var("TEST_LICK_ABORT", False))


def test_catch_trials_have_no_changes(raw):
    """Checks that trials don't have stimulus changes, and if they do verifies 
    that they change to the same image identity
    """
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        if trial["trial_params"]["catch"] is True and \
                len(trial["stimulus_changes"]) > 1 and \
                trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]:  # catch trials with stimulus changes to different stim is bad
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Catch trials have stimulus changes. Indices: {bad_trial_indices}"


def test_image_sequence(raw):
    """Tests that image name is contiguous across trials. If there was a 
    stimulus change in the previous trial, the initial image of the next change
    should be the final image of the previous change.
    """
    prev = get_initial_image(raw)
    for trial in raw["items"]["behavior"]["trial_log"]:
        if len(trial["stimulus_changes"]) > 0:
            initial_image = trial["stimulus_changes"][0][0][0]
            change_image = trial["stimulus_changes"][0][1][0]
            assert prev == initial_image, \
                "Initial image for a change should be the change image from the last trial with a stimulus change."
            prev = change_image


def test_event_log(raw):
    """Tests that trials dont have incorrect events based on whether theyre go
    or catch

    Notes
    -----
    - go trials should not have: sham_change, rejection, false_alarm
    - catch trials should not have: change, hit, miss
    """
    bad_trial_indices = []
    # check go trials
    for trial in filter_trials(raw, False):
        bad_events = [
            filter_events(trial, "sham_change"),
            filter_events(trial, "false_alarm"),
            filter_events(trial, "rejection"),
        ]
        if any(bad_events):
            bad_trial_indices.append(trial["index"])

    # check catch trials
    for trial in filter_trials(raw, True):
        bad_events = [
            filter_events(trial, "change"),
            filter_events(trial, "hit"),
            filter_events(trial, "miss"),
        ]
        if any(bad_events):
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Trials failing validation. Indices: {bad_trial_indices}"


@pytest.mark.skipif(
    skip_lick_abort_tests,
    reason="Requires this type of testing to be toggled.",
)
def test_abort_licks(raw):
    """Tests that trials in which the mouse licked before the change or 
    sham-change are listed as aborts in the trial log
    """
    bad_trial_indices = []
    for trial in raw["items"]["behavior"]["trial_log"]:
        early, within = classify_licks(trial)
        abort_events = filter_events(trial, "abort")
        if len(early) > 0 and len(abort_events) < 1:
            bad_trial_indices.append(trial["index"])

    assert len(bad_trial_indices) < 1, \
        f"Trials failing validation. Indices: {bad_trial_indices}"


def test_non_abort_event_log(raw):
    """Tests that:
    1) non-abort trials for which catch is True have the following response 
    types:
        a) no lick in the response window: rejection
        b) lick in the response window: false alarm 
    2) non-abort trials for which catch is False:
        a) no lick in the response window: miss
        b) lick in the response window: hit
    """
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
        auto_reward_events = filter_events(trial, "auto_reward")

        # auto rewarded trials have weird event logic, TODO: pair this with actual hit/miss events?
        if len(auto_reward_events) > 0:
            continue

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
        f"Trials failing validation. Indices: {bad_trial_indices}"


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
        f"Trials failing validation. Indices: {bad_trial_indices}"


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
        f"Trials failing validation. Indices: {bad_trial_indices}"
