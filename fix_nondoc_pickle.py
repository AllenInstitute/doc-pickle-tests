import os
import pickle
import copy
from typing import Dict
import logging
import uuid


logger = logging.getLogger(__name__)

transaction_log_path = f"{str(uuid.uuid4())}.log"
logger.addHandler(logging.FileHandler(transaction_log_path))


def is_faux_catch(trial: Dict) -> bool:
    return trial["trial_params"]["catch"] is True and \
        len(trial["stimulus_changes"]
            ) > 0 and trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]


def is_faux_go(trial: Dict, prev_image_name: str) -> bool:
    if trial["trial_params"]["catch"] is True:
        return False
    
    if trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]:
        return False
    
    return trial["stimulus_changes"][0][1][0] == prev_image_name


def list_to_contiguous_pairs(l):
    for i in range(0, len(l), 2):
        yield l[i:i+2]


def encode_image_name(image_name: str, contrast: int) -> str:
    return f"{image_name}-{contrast}"


def get_initial_image(data: Dict) -> str:
    initial_params = data["items"]["behavior"]["params"]["initial_image_params"]
    return encode_image_name(initial_params["Image"], initial_params["contrast"])


def fix_faux_catch_trial(trial: Dict) -> Dict:
    fixed = copy.deepcopy(trial)
    fixed["trial_params"]["catch"] = False
    fixed_events = []
    for event in fixed["events"]:
        if event[0] == "sham_change":
            event[0] = "change"
            fixed_events.append(event)
        elif event[0] == "correct_reject":
            event[0] = "miss"
            fixed_events.append(event)
        elif event[0] == "false_alarm":
            event[0] = "hit"
            fixed_events.append(event)
            fixed["has_omitted_reward"] = len(fixed["rewards"]) > 0 and \
                len(list(
                    filter(lambda event: event[0] == "auto_reward", fixed["events"]))) == 0
        else:
            fixed_events.append(event)
    
    fixed["events"] = fixed_events

    return fixed


def fix_faux_go_trial(trial: Dict) -> Dict:
    fixed = copy.deepcopy(trial)
    fixed["trial_params"]["catch"] = True
    fixed_events = []
    for event in fixed["events"]:
        if event[0] == "change":
            event[0] = "sham_change"
        elif event[0] == "miss":
            event[0] = "correct_reject"
        elif event[0] == "hit":
            event[0] = "false_alarm"
        else:
            pass
        fixed_events.append(event)
    
    # fixed["events"] = list(filter(lambda event: event[0] !=
    #                        "early_response", fixed["events"]))  # remove early response
    # fixed["events"] = list(
    #     filter(lambda event: event[0] != "abort", fixed["events"]))  # remove aborts
    
    fixed["events"] = fixed_events
    
    return fixed


def overwrite_prev_image(trial: Dict, new_image: str) -> None:
    """mutates object passed in
    """
    stimulus_change = trial["stimulus_changes"][0]
    trial["stimulus_changes"][0] = (
        (new_image, new_image, ), stimulus_change[1], stimulus_change[2], stimulus_change[3])


def fix_trials_initial_image(data: Dict) -> Dict:
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
    prev_image_name = fixed_images["items"]["behavior"]["trial_log"][0]["stimulus_changes"][0][0][0]
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

        if len(fixed_trial_log) > 0:  # in the weird situation where the first trial in a "success" is None trial
            prev_image_name = fixed_trial_log[-1]["stimulus_changes"][0][1][0]

    fixed_images["items"]["behavior"]["trial_log"] = fixed_trial_log

    return fixed_images


def fix_behavior_pickle(pickle_path: str, output_dir: str) -> str:
    with open(pickle_path, "rb") as f:
        data = pickle.load(f, encoding="latin1")
    
    logger.info("Fixing pickle at: %s" % pickle_path)
    fixed = fix_trials(data)

    output_path = os.path.join(
        output_dir,
        os.path.basename(pickle_path),
    )
    with open(output_path, "wb") as f:
        pickle.dump(fixed, f, protocol=0)

    return output_path


if __name__ == "__main__":
    import argparse
    import glob

    parser = argparse.ArgumentParser()
    parser.add_argument("pickle_search_pattern", type=str)
    parser.add_argument("output_dir", type=str)

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        if os.path.exists(args.output_dir):
            raise Exception(
                "Output directory path exists but isnt a directory. output_dir=%s" % args.output_dir)
        os.mkdir(args.output_dir)
        print("Created output dir at: %s" % args.output_dir)

    for target_pickle in glob.glob(args.pickle_search_pattern):
        try:
            fixed_pickle_path = fix_behavior_pickle(
                target_pickle, args.output_dir)
            print("Fixed pickle saved to: %s" % fixed_pickle_path)
        except Exception as e:
            print("Failed to fix pickle. target=%s: %s" % (target_pickle, e, ))
