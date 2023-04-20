def test_contiguous_image_identity(raw):
    for trial in raw["items"]["behavior"]["trial_log"]:
        assert trial["stimulus_changes"]
