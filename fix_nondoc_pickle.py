import os
import pickle
import copy
from typing import Dict
import logging
import uuid


logger = logging.getLogger(__name__)

transaction_log_path = f"{str(uuid.uuid4())}.log"
logger.addHandler(logging.FileHandler(transaction_log_path))
logger.setLevel(logging.DEBUG)


def is_faux_catch(trial: Dict) -> bool:
    """Whether or not a trial is a faux catch trial

    Notes
    -----
    - Intends to classify a trial as a "faux catch" if the trial is a catch
    trial but the image changes to a new image
    """
    return trial["trial_params"]["catch"] is True and \
        len(trial["stimulus_changes"]
            ) > 0 and trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]


def is_faux_go(trial: Dict, prev_image_name: str) -> bool:
    """Whether or not a trial is a faux go trial

    Notes
    -----
    - Intends to classify a trial as a "faux go" if the trial is a go trial but
    the image changes to the same image
    """
    if trial["trial_params"]["catch"] is True:
        return False

    if len(trial["stimulus_changes"]) < 1:
        return False

    if trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]:
        return False

    return trial["stimulus_changes"][0][1][0] == prev_image_name


def list_to_contiguous_pairs(l):
    for i in range(0, len(l), 2):
        yield l[i:i+2]


def encode_image_name(image_name: str, contrast: int) -> str:
    """Serializes image params as a string image name

    Notes
    -----
    - Downstream code expects a string image name
    """
    return f"{image_name}-{contrast}"


def get_initial_image(data: Dict) -> str:
    initial_params = data["items"]["behavior"]["params"]["initial_image_params"]
    return encode_image_name(initial_params["Image"], initial_params["contrast"])


def fix_faux_catch_trial(trial: Dict) -> Dict:
    """Fixes trials that are incorrectly classified as catch trials because the
    image changes to a new value

    Notes
    -----
    - Relabels these trials as go trials
    - changes event labels in the event log to reflect what they should be 
    for a go trial
    """
    fixed = copy.deepcopy(trial)
    fixed["trial_params"]["catch"] = False
    fixed_events = []
    for event in fixed["events"]:
        if event[0] == "sham_change":
            event[0] = "change"
        elif event[0] == "rejection":
            event[0] = "miss"
        elif event[0] == "false_alarm":
            event[0] = "hit"
            fixed["has_omitted_reward"] = len(fixed["rewards"]) > 0 and \
                len(list(
                    filter(lambda event: event[0] == "auto_reward", fixed["events"]))) == 0
        else:
            pass
        fixed_events.append(event)

    fixed["events"] = fixed_events

    return fixed


def fix_faux_go_trial(trial: Dict) -> Dict:
    """Fixes trials that are incorrectly classified as go trials because the
    image never changes and are not aborted or the image changes to the same
    image name

    Notes
    -----
    - Relabels these trials as catch trials
    - changes event labels in the event log to reflect what they should be 
    for a catch trial
    """
    fixed = copy.deepcopy(trial)
    fixed["trial_params"]["catch"] = True
    fixed_events = []
    for event in fixed["events"]:
        if event[0] == "change":
            event[0] = "sham_change"
        elif event[0] == "miss":
            event[0] = "rejection"
        elif event[0] == "hit":
            event[0] = "false_alarm"
        else:
            pass
        fixed_events.append(event)

    fixed["events"] = fixed_events

    return fixed


def overwrite_prev_image(trial: Dict, new_image: str) -> None:
    """mutates object passed in
    """
    stimulus_change = trial["stimulus_changes"][0]
    trial["stimulus_changes"][0] = (
        (new_image, new_image, ), stimulus_change[1], stimulus_change[2], stimulus_change[3])


def fix_trials_initial_image(data: Dict) -> Dict:
    """Fixes the initial image name of the stimulus change of each trial

    Notes
    -----
    - ensures that the initial image name of each change is accurate
    - some bad trials had the incorrect initial image name because a change
    that was scheduled never occurred
    """
    fixed = copy.deepcopy(data)
    prev = get_initial_image(data)
    for trial in fixed["items"]["behavior"]["trial_log"]:
        stimulus_changes = trial["stimulus_changes"]
        if len(stimulus_changes) > 0:
            if stimulus_changes[0][0][0] != prev:
                overwrite_prev_image(trial, prev)
            prev = stimulus_changes[0][1][0]
        else:
            pass
    return fixed


def fix_images(data: Dict) -> Dict:
    fixed = copy.deepcopy(data)
    images_params = fixed["items"]["behavior"]["stimuli"].pop("images-params")
    fixed["items"]["behavior"]["stimuli"]["images"] = images_params
    set_log = fixed["items"]["behavior"]["stimuli"]["images"]["set_log"]
    # kinda vital since we're ignoring the first two and making some assumptions
    assert set_log[0][3] == 0 and set_log[1][3] == 0
    fixed_set_log = [
        ("Image", get_initial_image(fixed), set_log[0][2], set_log[0][3], ),
    ]

    stim_groups = {}
    for logs in list_to_contiguous_pairs(set_log[2:]):
        assert logs[0][0] == "Image" and logs[1][0] == "contrast"
        image_name = encode_image_name(logs[0][1], logs[1][1])
        fixed_set_log.append(
            ("Image", image_name, logs[0][2], logs[0][3], )
        )
        stim_groups[image_name] = [image_name, ]

    fixed["items"]["behavior"]["stimuli"]["images"]["set_log"] = fixed_set_log
    fixed["items"]["behavior"]["stimuli"]["images"]["stim_groups"] = stim_groups
    fixed["items"]["behavior"]["stimuli"]["images"]["obj_type"] = "DoCImageStimulus"

    for trial in fixed["items"]["behavior"]["trial_log"]:
        stimulus_changes = trial["stimulus_changes"]
        if len(trial["stimulus_changes"]) > 0:
            # ensure its the shape were assuming it is
            assert len(stimulus_changes) == 1
            assert len(stimulus_changes[0]) == 4
            assert len(stimulus_changes[0][0]) == 2
            assert len(stimulus_changes[0][1]) == 2
            from_image = encode_image_name(
                stimulus_changes[0][0][1]["Image"],
                stimulus_changes[0][0][1]["contrast"],
            )
            to_image = encode_image_name(
                stimulus_changes[0][1][1]["Image"],
                stimulus_changes[0][1][1]["contrast"],
            )
            trial["stimulus_changes"] = [
                (
                    (from_image, from_image, ),
                    (to_image, to_image, ),
                    stimulus_changes[0][2],
                    stimulus_changes[0][3],
                )
            ]

    return fixed


def fix_trials(data: Dict) -> Dict:
    fixed = copy.deepcopy(data)
    fixed_images = fix_images(fixed)
    fixed_trial_log = []
    initial_image_params = fixed["items"]["behavior"]["params"]["initial_image_params"]
    prev_image_name = encode_image_name(
        initial_image_params["Image"], initial_image_params["contrast"])
    for trial in fixed_images["items"]["behavior"]["trial_log"]:
        if trial["success"] is None:
            pass
        elif is_faux_go(trial, prev_image_name):
            fixed_trial_log.append(
                fix_faux_go_trial(trial)
            )
            logger.info("Fixed faux go trial at: %s" % trial["index"])
        elif is_faux_catch(trial):
            fixed_trial_log.append(
                fix_faux_catch_trial(trial)
            )
            logger.info("Fixed faux catch trial at: %s" % trial["index"])
        else:
            fixed_trial_log.append(trial)

        # in the weird situation where the first trial in a "success" is None trial
        if len(fixed_trial_log) > 0 and len(fixed_trial_log[-1]["stimulus_changes"]) > 0:
            prev_image_name = fixed_trial_log[-1]["stimulus_changes"][0][1][0]

    fixed_images["items"]["behavior"]["trial_log"] = fixed_trial_log

    return fixed_images


def filter_events(trial: dict, name_fiter: str) -> list:
    """Filters event in a trial log entry based on event name.
    """
    return [
        event for event in trial["events"]
        if event[0].startswith(name_fiter)
    ]


def lick_within_response_window(lickEvent, response_window_lower: int, response_window_upper: int):
    return lickEvent[3] >= response_window_lower and lickEvent[3] <= response_window_upper


def fix_lick_disabled_trial_log(log) -> None:
    """mutates object passed in
    """
    if log["licks_enabled"] is True:
        return

    disabled_licks = filter_events(log, "licks disabled.")
    response_window_events = filter_events(log, "response_window")
    if not len(response_window_events) == 2:
        return

    within_window_licks = list(filter(
        lambda event: lick_within_response_window(
            event,
            response_window_events[0][3],
            response_window_events[1][3],
        ),
        disabled_licks
    ))

    if not len(within_window_licks) > 0:
        return

    first_disabled_lick = within_window_licks[0]
    # if a miss occurred relabel it as a hit
    miss_events = filter_events(log, "miss")
    if len(miss_events) > 0:
        # fix event log
        fixed_events = []
        hit_added = False
        for event in log["events"]:
            if event[0].startswith("miss"):
                continue

            if event[3] == first_disabled_lick[3] and not hit_added:
                if not event[0].startswith("licks disabled."):
                    continue
                fixed_events.append([
                    "hit",
                    first_disabled_lick[1],
                    first_disabled_lick[2],
                    first_disabled_lick[3],
                ])
                hit_added = True
            else:
                fixed_events.append(event)

        log["events"] = fixed_events


# def fix_lick_disabled_trial_log(log) -> None:
#     """mutates object passed in
#     """
#     if log["licks_enabled"] is True:
#         return

#     disabled_licks = filter_events(log, "licks disabled.")
#     response_window_events = filter_events(log, "response_window")
#     if not len(response_window_events) == 2:
#         return

#     within_window_licks = list(filter(
#         lambda event: lick_within_response_window(
#             event,
#             response_window_events[0][3],
#             response_window_events[1][3],
#         ),
#         disabled_licks
#     ))

#     if not len(within_window_licks) > 0:
#         return

#     first_disabled_lick = within_window_licks[0]
#     # if a miss occurred relabel it as a hit
#     miss_events = filter_events(log, "miss")
#     if len(miss_events) > 0:
#         # fix event log
#         fixed_events = []
#         hit_added = False
#         for event in log["events"]:
#             if event[0].startswith("miss"):
#                 continue

#             if event[3] == first_disabled_lick[3] and not hit_added:
#                 if not event[0].startswith("licks disabled."):
#                     continue
#                 fixed_events.append([
#                     "hit",
#                     first_disabled_lick[1],
#                     first_disabled_lick[2],
#                     first_disabled_lick[3],
#                 ])
#                 hit_added = True
#             else:
#                 fixed_events.append(event)

#         log["events"] = fixed_events


def is_early_lick(
    lick,
    response_window_lower: float,
    stimulus_change_events: list,
) -> bool:
    lick_time, _ = lick
    if not lick_time < response_window_lower:
        return False

    # licks dont count as aborts if theyre before the response window but after
    # the stimulus change
    if len(stimulus_change_events) > 0:
        return lick_time < stimulus_change_events[0][2]
    else:
        return True


def lick_disabled_event_to_lick(event):
    assert event[0].startswith("licks disabled."), \
        f"Unexpected event name: {event[0]}"
    return event[2], event[3]


def classify_licks_no_reward_epoch(trial):
    """licks arent populated for "no_reward", they also have wierd event names
    """
    response_window_events = filter_events(trial, "response_window")
    lick_events = filter_events(trial, "licks disabled.")
    licks = list(map(lick_disabled_event_to_lick, lick_events))

    if len(response_window_events) < 2:
        abort_events = filter_events(trial, "abort")
        if len(abort_events) < 1:
            raise Exception("No response window but not aborted!")
        return licks, []

    response_window_lower = response_window_events[0][2]
    response_window_upper = response_window_events[1][2]
    stimulus_change_events = filter_events(trial, "stimulus_changed")
    early = list(filter(
        lambda lick: is_early_lick(
            lick, response_window_lower, stimulus_change_events),
        licks,
    ))
    within_window = list(filter(
        lambda lick: response_window_lower < lick[0] < response_window_upper,
        licks,
    ))

    return early, within_window


def fix_no_reward_catch(log):
    early, within_window = \
        classify_licks_no_reward_epoch(log)

    if len(early) > 0:
        new_event_name = "early_response"
        lick_time, _ = early[0]
    elif len(within_window) > 0:
        new_event_name = "false_alarm"
        lick_time, _ = within_window[0]
    else:
        return

    fixed = []
    added_early_response = False
    for event in log["events"]:
        if event[0].startswith("licks disabled.") and \
                event[2] == lick_time and \
                not added_early_response:
            fixed.append(event)
            fixed.append([
                new_event_name,
                event[1],
                event[2],
                event[3],
            ])
            added_early_response = True
        elif event[0].startswith("rejection"):
            pass
        else:
            fixed.append(event)
    log["events"] = fixed


def fix_no_reward_go(log):
    early, within_window = \
        classify_licks_no_reward_epoch(log)

    if len(early) > 0:
        new_event_name = "early_response"
        lick_time, _ = early[0]
    elif len(within_window) > 0:
        new_event_name = "hit"
        lick_time, _ = within_window[0]
    else:
        return

    fixed = []
    added_early_response = False
    for event in log["events"]:
        if event[0].startswith("licks disabled.") and \
                event[2] == lick_time and \
                not added_early_response:
            fixed.append(event)
            fixed.append([
                new_event_name,
                event[1],
                event[2],
                event[3],
            ])
            added_early_response = True
        elif event[0].startswith("miss"):
            pass
        else:
            fixed.append(event)
    log["events"] = fixed


def fix_lick_disabled_log(log):
    if log["licks_enabled"]:
        return

    is_catch = log["trial_params"]["catch"]
    if is_catch is True:
        rejection_events = filter_events(log, "rejection")
        if len(rejection_events) < 1:
            return

        fix_no_reward_catch(log)
    elif is_catch is False:
        miss_events = filter_events(log, "miss")
        if len(miss_events) < 1:
            return

        fix_no_reward_go(log)
    else:
        raise Exception("Unexpected value for is_catch: %s" % is_catch)


def fix_behavior_pickle(pickle_path: str, output_dir: str) -> str:
    with open(pickle_path, "rb") as f:
        data = pickle.load(f, encoding="latin1")

    logger.info("Fixing pickle at: %s" % pickle_path)
    fixed = fix_trials(data)
    for log in data["items"]["behavior"]["trial_log"]:
        fix_lick_disabled_log(log)

    output_path = os.path.join(
        output_dir,
        os.path.basename(pickle_path),
    )
    with open(output_path, "wb") as f:
        pickle.dump(fixed, f, protocol=0)

    return output_path


if __name__ == "__main__":
    import yaml
    import glob
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("target_pickle_list", type=str)
    parser.add_argument("output_dir", type=str)

    args = parser.parse_args()

    with open(args.target_pickle_list, "r") as f:
        output_dirs = yaml.safe_load(f)

    target_pickles = []
    for output_dir in output_dirs:
        pattern = glob.glob(output_dir + "/*.behavior.pkl")
        pickles = list(glob.glob(output_dir + "/*.behavior.pkl"))
        if len(pickles) > 1:
            logger.error(
                "More than one pickle detected in output dir: %s" % output_dir)
        elif not len(pickles) > 0:
            logger.error("No pickles in directory: %s" % output_dir)
            continue

        target_pickles.append(pickles[0])

    if not os.path.isdir(args.output_dir):
        if os.path.exists(args.output_dir):
            raise Exception(
                "Output directory path exists but isnt a directory. output_dir=%s" % args.output_dir)
        os.makedirs(args.output_dir)
        print("Created output dir at: %s" % args.output_dir)

    for target_pickle in target_pickles:
        try:
            fixed_pickle_path = fix_behavior_pickle(
                target_pickle, args.output_dir)
            logger.info("Fixed pickle saved to: %s" % fixed_pickle_path)
        except Exception as e:
            print("Error fixing pickle: %s" % target_pickle)
            logger.error("Failed to fix pickle. target=%s." %
                         (target_pickle, ), exc_info=True)
