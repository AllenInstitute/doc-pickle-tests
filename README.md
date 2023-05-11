Run known test cases on doc camstim pickles and the vba dataframes they generate.

Pickles are supplied to the tests via a glob pattern stored in an environment variable at: `PICKLE_SEARCH_PATTERN`

## How are the pickles being "fixed"

This code is intended to "fix" behavior data pickles that were generated from an older buggy version of the task.

### Success None Trials

There are "go" trials which have a duration that is longer than the maximum expected trial duration. The trial dict in the `trial_log` of the pickle data contains the key, value `"success": None`. These trials are removed from the `trial_log` but the trial indices of the other trials are not updated (eg: if trials 1,3 are good but trial 2 isnt, trial 3 will still have `"index": 3` despite trial 2 being removed).

### Faux-go Trials

There are "go" trials which change to the same image. They are changed to "catch" trials. Within the `"event_log"` of their respective trial dicts,

### Faux-catch Trials

## How to run

### Windows

Initialize

```
init_env
```

Run

```
exec_tests
```

### Docker

Initialize

```
make setup_image
```

#### Run Tests

```
make run_tests
```

#### Run Fixes

```
make fix_pickles
```
