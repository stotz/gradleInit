#!/usr/bin/env bash
#
# run_all_tests.sh - run every tracked test module and report a summary.
#
# Only git-tracked test_*.py files run: local leftovers (an untracked
# test_versions.py without shebang, an old test_template_compilation.py) are
# skipped and listed. Exit code 1 when any module fails.

set -u

cd "$(dirname "$0")" || exit 1

echo "### run: ./gradleInit.py --version"
./gradleInit.py --version || exit 1

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  mapfile -t tests < <(git ls-files -- 'test_*.py' | sort)
  mapfile -t untracked < <(comm -23 <(ls test_*.py 2>/dev/null | sort) <(printf '%s\n' "${tests[@]}"))
else
  mapfile -t tests < <(ls test_*.py | sort)
  untracked=()
fi

failed=()
for test in "${tests[@]}"; do
  echo ""
  echo "### run: $test"
  if ! python3 "$test"; then
    failed+=("$test")
  fi
done

echo ""
echo "======================================================================"
echo "  ${#tests[@]} test module(s), ${#failed[@]} failed"
for t in "${failed[@]:-}"; do
  [ -n "$t" ] && echo "  FAILED: $t"
done
if [ "${#untracked[@]}" -gt 0 ] && [ -n "${untracked[0]}" ]; then
  echo "  skipped (not tracked by git): ${untracked[*]}"
fi
echo "======================================================================"

[ "${#failed[@]}" -eq 0 ]
