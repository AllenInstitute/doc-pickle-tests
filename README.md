Run known test cases on doc camstim pickles and the vba dataframes they generate.

Pickles are supplied to the tests via a glob pattern stored in an environment variable at: `PICKLE_SEARCH_PATTERN`

## How are the pickles being "fixed"

Bur

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

Run

```
make run_tests
```
