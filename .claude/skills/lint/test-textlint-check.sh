#!/usr/bin/env bash

set -uo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
checker="$script_dir/textlint-check.sh"
fixtures="$script_dir/fixtures/textlint"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/wiki-textlint-test.XXXXXX")
cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

problematic_output="$work_dir/problematic.out"
problematic_status=0
bash "$checker" "$fixtures/problematic.md" > "$problematic_output" || problematic_status=$?

if [ "$problematic_status" -ne 1 ]; then
  echo "problematic fixture should fail with required findings: $problematic_status" >&2
  exit 1
fi

for rule in \
  no-zero-width-spaces \
  no-nfd \
  no-hankaku-kana \
  ja-unnatural-alphabet \
  no-unmatched-pair \
  no-dropping-the-ra \
  no-double-negative-ja \
  ja-no-abusage \
  no-ai-colon-continuation \
  no-ai-hype-expressions
do
  if ! grep -q "rule=.*${rule}" "$problematic_output"; then
    echo "missing expected finding: $rule" >&2
    exit 1
  fi
done

revised_output="$work_dir/revised.out"
if ! bash "$checker" "$fixtures/revised.md" > "$revised_output"; then
  cat "$revised_output" >&2
  echo "revised fixture should pass" >&2
  exit 1
fi
if ! grep -q 'required=0 review=0 info=0' "$revised_output"; then
  cat "$revised_output" >&2
  echo "revised fixture should have no findings" >&2
  exit 1
fi

node -e 'require("fs").writeFileSync(process.argv[1], "制御\u000b文字を含む。\n")' "$work_dir/control.md"
control_output="$work_dir/control.out"
control_status=0
bash "$checker" "$work_dir/control.md" > "$control_output" || control_status=$?
if [ "$control_status" -ne 1 ] || ! grep -q 'no-invalid-control-character' "$control_output"; then
  echo "invalid control character was not classified as required" >&2
  exit 1
fi

echo "textlint-check tests passed"
