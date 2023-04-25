import argparse
import os
import pickle
import copy
from typing import Dict

# from visual_behavior.translator.core import create_extended_dataframe
# from visual_behavior.schemas.extended_trials import ExtendedTrialSchema
# from visual_behavior.translator import foraging2


def is_pseudo_catch(trial: Dict) -> bool:
    return trial["trial_params"]["catch"] is True and \
        len(trial["stimulus_changes"]
            ) > 0 and trial["stimulus_changes"][0][0][0] != trial["stimulus_changes"][0][1][0]


def is_pseudo_go(trial: Dict) -> bool:
    return trial["trial_params"]["catch"] is False and \
        len(trial["stimulus_changes"]) < 1


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
        if event[0] in ["no_lick", "sham_change"]:
            pass
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
    fixed["events"] = list(filter(lambda event: event[0] !=
                           "early_response", fixed["events"]))  # remove early response
    # remove early response
    fixed["events"] = list(
        filter(lambda event: event[0] != "abort", fixed["events"]))
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
    for trial in fixed_images["items"]["behavior"]["trial_log"]:
        if trial["success"] is None:
            pass
        elif is_pseudo_go(trial):
            fixed_trial_log.append(
                fix_faux_go_trial(trial)
            )
        elif is_pseudo_catch(trial):
            fixed_trial_log.append(
                fix_faux_catch_trial(trial)
            )
        else:
            fixed_trial_log.append(trial)

    fixed_images["items"]["behavior"]["trial_log"] = fixed_trial_log

    return fixed_images


def fix_behavior_pickle(pickle_path: str, output_dir: str) -> str:
    with open(pickle_path, "rb") as f:
        data = pickle.load(f, encoding="latin1")

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

    parser = argparse.ArgumentParser()
    parser.add_argument("target_pickle", type=str)
    parser.add_argument("output_dir", type=str)

    args = parser.parse_args()

    fixed_pickle_path = fix_behavior_pickle(
        args.target_pickle, args.output_dir)

    print("Fixed pickle saved to: %s" % fixed_pickle_path)
