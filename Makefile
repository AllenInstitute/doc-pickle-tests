check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))

setup_image:
	docker build --no-cache -t doc-pickle-tests .

check_mtrain_api_env_vars:
	$(call check_defined, PICKLE_SEARCH_PATTERN)

run_tests: check_mtrain_api_env_vars
	docker run --network="host" \
	-v ${PWD}/tests:/tests \
	-e PICKLE_SEARCH_PATTERN=${PICKLE_SEARCH_PATTERN}
	doc-pickle-tests pytest /tests -vv --cache-clear
