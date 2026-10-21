#!/usr/bin/env bash

set -o pipefail -eux

declare -a args
declare -a docker_args=()
IFS='/:' read -ra args <<< "$1"

image="${args[1]}"

if [ "${#args[@]}" -gt 2 ]; then
    target="shippable/posix/group${args[2]}/"
else
    target="shippable/posix/"
fi

# Group 2 contains the virt-install targets. Keep the existing group 1 jobs
# unchanged: enabling privileges there would also enable unrelated old tests.
if [ "${args[2]:-}" = "2" ]; then
    docker_args+=(--docker-privileged)
fi

# shellcheck disable=SC2086
ansible-test integration --color -v --retry-on-error "${target}" ${COVERAGE:+"$COVERAGE"} ${CHANGED:+"$CHANGED"} ${UNSTABLE:+"$UNSTABLE"} \
    --docker "${image}" "${docker_args[@]}"
