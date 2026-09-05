#!/usr/bin/env bash

set -uo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_path="${script_dir}/textlint.config.json"

if [ "$#" -eq 0 ]; then
  echo "usage: bash .agents/skills/lint/textlint-check.sh <file-or-glob> [...]" >&2
  exit 2
fi

result_file=$(mktemp "${TMPDIR:-/tmp}/wiki-textlint.XXXXXX.json")
cleanup() {
  rm -f "$result_file"
}
trap cleanup EXIT

textlint_status=0
pnpm exec textlint -c "$config_path" -f json -o "$result_file" "$@" || textlint_status=$?

# textlintはfindingがあるだけで1を返す。2以上だけを実行異常とする。
if [ "$textlint_status" -gt 1 ]; then
  echo "TEXTLINT_EXEC_ERROR textlint exited with status ${textlint_status}" >&2
  exit 2
fi

node "$script_dir/textlint-report.mjs" "$result_file"
