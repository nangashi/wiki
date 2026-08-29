#!/usr/bin/env bash
# .claude/skills/lint/lint-check.sh
#
# 構造的lintチェックを実行し、結果を標準出力に出力する。
# /lint スキルがこのスクリプトを先に実行し、出力をもとにLLM分析を行う。
#
# 担当するチェック:
#   CHECK-1: リンク切れ（同一コレクション内 [[slug]] とクロスリンク [[col:slug]]）
#   CHECK-2: 孤立ページ（全コレクション横断）
#   CHECK-3: リンク漏れ候補（誤検知あり → LLMが最終判断）
#   CHECK-5: 粒度メトリクス（数値計測のみ → LLMが最終判断）
#   CHECK-8: 低価値ページ候補（誤検知あり → LLMが最終判断）
#   CHECK-8b: insight外部ソース構造（旧frontmatterへfallbackしない）
#   CHECK-9: 記事品質評価待ち（insightのみ。rubric versionと内容hashを照合）
#
# LLMが担当するチェック:
#   CHECK-4: 重複概念（意味的類似性）
#   CHECK-6: 矛盾（セマンティック推論）
#   CHECK-7: 未接続の合成機会
#
# 補助出力:
#   SAMPLE_EVALUATION: 品質ドリフト監査用にランダムに3ページ選出
#   OPEN_SUGGESTION: suggestions/ 配下で有効なfrontmatterを持つopen提案
#
# 使い方:
#   bash lint-check.sh --collection name:path [--collection name2:path2 ...]
# テスト専用内部引数:
#   --evaluations-root path --rubric-file path --suggestions-root path
#
# 例:
#   bash .claude/skills/lint/lint-check.sh \
#     --collection insight:wiki/insight/pages \
#     --collection it:wiki/it/pages

set -uo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# ── 引数パース ────────────────────────────────────────────────────────
declare -A collection_paths  # collection_paths[name]=path
declare -a collection_names  # 順序保持用
evaluations_root="evaluations/insight"
rubric_file="wiki/insight/references/article-quality-rubric.md"
suggestions_root="suggestions"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --collection)
      IFS=':' read -r col_name col_path <<< "$2"
      collection_paths["$col_name"]="$col_path"
      collection_names+=("$col_name")
      shift 2
      ;;
    --evaluations-root)
      evaluations_root="$2"
      shift 2
      ;;
    --rubric-file)
      rubric_file="$2"
      shift 2
      ;;
    --suggestions-root)
      suggestions_root="$2"
      shift 2
      ;;
    *)
      # 後方互換: 引数なしで旧形式 wiki/pages を受け付ける
      collection_paths["default"]="$1"
      collection_names+=("default")
      shift
      ;;
  esac
done

if [ ${#collection_names[@]} -eq 0 ]; then
  # デフォルト（後方互換）
  collection_paths["insight"]="wiki/insight/pages"
  collection_names+=("insight")
fi

# ── 各コレクションのページファイルを収集 ─────────────────────────────
declare -A col_slug_to_title   # "col/slug" → title
declare -A col_slug_to_file    # "col/slug" → filepath
declare -A slug_to_col         # slug → collection name（全体一覧用）

total=0

for col in "${collection_names[@]}"; do
  dir="${collection_paths[$col]}"
  if [ ! -d "$dir" ]; then
    echo "WARN: コレクション '${col}' のディレクトリが存在しません: ${dir}"
    continue
  fi

  while IFS= read -r f; do
    slug=$(basename "$f" .md)
    title=$(grep -m1 '^title:' "$f" | sed 's/^title:[[:space:]]*//' | sed 's/["\x27]//g') || true
    col_slug_to_title["${col}/${slug}"]="${title:-$slug}"
    col_slug_to_file["${col}/${slug}"]="$f"
    slug_to_col["$slug"]="$col"
    total=$((total + 1))
  done < <(find "$dir" -name "*.md" ! -name ".gitkeep" | sort)
done

echo "PAGES_TOTAL: $total"
echo "COLLECTIONS: ${collection_names[*]}"
echo ""

if [ "$total" -eq 0 ]; then
  echo "INFO: ページが存在しません。チェックをスキップします。"
  exit 0
fi

# ── CHECK-1: リンク切れ ───────────────────────────────────────────────
echo "=== CHECK-1: リンク切れ ==="
c1=0

for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"
  slug="${key##*/}"

  # [[slug]] 形式（同一コレクション内）
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    # クロスリンク形式 [[col:slug]] は別処理
    [[ "$ref" == *:* ]] && continue
    if [[ -z "${col_slug_to_title["${col}/${ref}"]+_}" ]]; then
      echo "BROKEN  collection=${col}  src=${slug}  ref=${ref}  type=local"
      c1=$((c1 + 1))
    fi
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | grep -v ':' || true)

  # [[col:slug]] 形式（クロスリンク）
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    [[ "$ref" != *:* ]] && continue
    ref_col="${ref%%:*}"
    ref_slug="${ref##*:}"
    if [[ -z "${col_slug_to_title["${ref_col}/${ref_slug}"]+_}" ]]; then
      echo "BROKEN  collection=${col}  src=${slug}  ref=${ref}  type=cross"
      c1=$((c1 + 1))
    fi
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | grep ':' || true)
done

[ "$c1" -eq 0 ] && echo "OK: リンク切れなし"
echo "COUNT: $c1"
echo ""

# ── CHECK-1b: エイリアス記法 ─────────────────────────────────────────
echo "=== CHECK-1b: エイリアス記法 ==="
c1b=0

for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"
  slug="${key##*/}"

  while IFS= read -r link; do
    echo "ALIAS  collection=${col}  src=${slug}  link=${link}"
    c1b=$((c1b + 1))
  done < <(grep -oh '\[\[[^]|]*|[^]]*\]\]' "$f" 2>/dev/null || true)
done

[ "$c1b" -eq 0 ] && echo "OK: エイリアス記法なし"
echo "COUNT: $c1b"
echo ""

# ── CHECK-2: 孤立ページ ──────────────────────────────────────────────
echo "=== CHECK-2: 孤立ページ ==="
declare -A referenced  # referenced["col/slug"]=1 なら参照されている

for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"

  # [[slug]] → 同一コレクション内参照
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    [[ "$ref" == *:* ]] && continue
    referenced["${col}/${ref}"]=1
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | grep -v ':' || true)

  # [[col:slug]] → クロスリンク参照
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    [[ "$ref" != *:* ]] && continue
    ref_col="${ref%%:*}"
    ref_slug="${ref##*:}"
    referenced["${ref_col}/${ref_slug}"]=1
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | grep ':' || true)
done

c2=0
for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"
  slug="${key##*/}"
  has_out=$(grep -c '\[\[[^]]*\]\]' "$f" 2>/dev/null) || has_out=0
  has_in=0
  [[ -n "${referenced[$key]+_}" ]] && has_in=1

  if [[ "$has_out" -eq 0 && "$has_in" -eq 0 ]]; then
    echo "ORPHAN  collection=${col}  slug=${slug}  title=${col_slug_to_title[$key]}"
    c2=$((c2 + 1))
  fi
done

[ "$c2" -eq 0 ] && echo "OK: 孤立ページなし"
echo "COUNT: $c2"
echo ""

# ── CHECK-3: リンク漏れ候補 ──────────────────────────────────────────
echo "=== CHECK-3: リンク漏れ候補 (誤検知の可能性あり - LLMで最終確認) ==="
c3=0

for src_key in "${!col_slug_to_file[@]}"; do
  src_f="${col_slug_to_file[$src_key]}"
  src_col="${src_key%%/*}"
  src_slug="${src_key##*/}"
  body=$(awk 'BEGIN{f=0} /^---/{f++; next} f>=2{print}' "$src_f")

  for tgt_key in "${!col_slug_to_title[@]}"; do
    tgt_col="${tgt_key%%/*}"
    tgt_slug="${tgt_key##*/}"
    [[ "$src_key" == "$tgt_key" ]] && continue
    tgt_title="${col_slug_to_title[$tgt_key]}"
    [[ ${#tgt_title} -lt 4 ]] && continue

    # タイトルが本文に登場
    if echo "$body" | grep -qF "$tgt_title"; then
      # 同一コレクション: [[tgt_slug]] がなければ漏れ
      if [[ "$src_col" == "$tgt_col" ]]; then
        if ! grep -q "\[\[${tgt_slug}\]\]" "$src_f"; then
          echo "MISSING_LINK  collection=${src_col}  src=${src_slug}  mentions='${tgt_title}'  suggest=[[${tgt_slug}]]"
          c3=$((c3 + 1))
        fi
      else
        # クロスコレクション: [[tgt_col:tgt_slug]] がなければ漏れ
        if ! grep -q "\[\[${tgt_col}:${tgt_slug}\]\]" "$src_f"; then
          echo "MISSING_LINK  collection=${src_col}  src=${src_slug}  mentions='${tgt_title}'  suggest=[[${tgt_col}:${tgt_slug}]]"
          c3=$((c3 + 1))
        fi
      fi
    fi
  done
done

[ "$c3" -eq 0 ] && echo "OK: リンク漏れ候補なし"
echo "COUNT: $c3"
echo ""

# ── CHECK-5: 粒度メトリクス ──────────────────────────────────────────
echo "=== CHECK-5: 粒度メトリクス (最終判断はLLMが行う) ==="
c5=0

for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"
  slug="${key##*/}"
  chars=$(wc -m < "$f")
  body_chars=$(awk 'BEGIN{f=0} /^---/{f++; next} f>=2{print}' "$f" | wc -m)
  links=$(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | wc -l) || links=0
  sections=$(grep -c '^## ' "$f" 2>/dev/null) || sections=0
  flags=""
  # 「広すぎる」目安: 本文2500字以上（複数の独立概念を含むかはLLMが判断。コーパス実測: 中央値約1500字・最大約2900字）
  [[ "$body_chars" -gt 2500 ]] && flags="${flags} LARGE(${body_chars}chars)"
  [[ "$chars" -lt 150 ]]  && flags="${flags} TINY(${chars}chars)"
  [[ "$links" -gt 10 ]]   && flags="${flags} MANY_LINKS(${links})"

  if [[ -n "$flags" ]]; then
    echo "METRICS  collection=${col}  slug=${slug}  chars=${chars}  body_chars=${body_chars}  links=${links}  sections=${sections}  flags=${flags}"
    c5=$((c5 + 1))
  fi
done

[ "$c5" -eq 0 ] && echo "OK: メトリクス異常なし"
echo "COUNT: $c5"
echo ""

# ── CHECK-8: 低価値ページ候補 ────────────────────────────────────────
echo "=== CHECK-8: 低価値ページ候補 (最終判断はLLMが行う) ==="
c8=0

for key in "${!col_slug_to_file[@]}"; do
  f="${col_slug_to_file[$key]}"
  col="${key%%/*}"
  slug="${key##*/}"
  chars=$(wc -m < "$f")
  has_out=$(grep -c '\[\[[^]]*\]\]' "$f" 2>/dev/null) || has_out=0
  has_in=0
  [[ -n "${referenced[$key]+_}" ]] && has_in=1

  if [[ "$chars" -lt 150 && "$has_out" -eq 0 && "$has_in" -eq 0 ]]; then
    echo "LOW_VALUE  collection=${col}  slug=${slug}  reason=TINY_ORPHAN  chars=${chars}"
    c8=$((c8 + 1))
    continue
  fi

  body=$(awk 'BEGIN{f=0} /^---/{f++; next} f>=2{print}' "$f")
  body_chars=$(echo "$body" | wc -m)
  if [[ "$body_chars" -lt 100 ]] && echo "$body" | grep -q '→.*\[\['; then
    echo "LOW_VALUE  collection=${col}  slug=${slug}  reason=REDIRECT  body_chars=${body_chars}"
    c8=$((c8 + 1))
  fi
done

[ "$c8" -eq 0 ] && echo "OK: 低価値ページ候補なし"
echo "COUNT: $c8"
echo ""

# ── CHECK-8b: insight外部ソース構造 ─────────────────────────────────
echo "=== CHECK-8b: insight外部ソース構造 ==="
declare -a insight_source_files
for key in "${!col_slug_to_file[@]}"; do
  [[ "${key%%/*}" == "insight" ]] && insight_source_files+=("${col_slug_to_file[$key]}")
done
if [ ${#insight_source_files[@]} -eq 0 ]; then
  echo "INFO: insightページなし"
  echo "COUNT: 0"
else
  if ! python3 "${script_dir}/insight_source_validator.py" "${insight_source_files[@]}"; then
    echo "INFO: insight外部ソース診断あり。lint全体は継続します"
  fi
fi
echo ""

# ── CHECK-9: 記事品質評価待ち（insightコレクションのみ） ──────────────
echo "=== CHECK-9: 記事品質評価状態 (insightコレクションのみ) ==="

current_version=""
if [ -f "$rubric_file" ]; then
  current_version=$(grep -m1 -oE 'rubric_version:[[:space:]]*[0-9]+' "$rubric_file" | grep -oE '[0-9]+') || true
fi

eval_current=0
eval_missing=0
eval_old_rubric=0
eval_changed=0
eval_malformed=0
eval_output_invalid=0
invalid_metadata_history=0
invalid_output_history=0
insight_total=0
declare -a insight_slugs

parsed_target=""
parsed_blob=""
parsed_version=""
parsed_evaluated_at=""
parsed_run_id=""

validate_evaluation_metadata() {
  local eval_file="$1"
  local expected_slug="$2"
  local base filename_timestamp filename_version filename_run_id
  local frontmatter frontmatter_lines normalized_at

  parsed_target=""
  parsed_blob=""
  parsed_version=""
  parsed_evaluated_at=""
  parsed_run_id=""

  base=$(basename "$eval_file")
  if [[ ! "$base" =~ ^([0-9]{8}T[0-9]{6}Z)-v([0-9]+)-([a-z0-9]{8,32})\.md$ ]]; then
    return 1
  fi
  filename_timestamp="${BASH_REMATCH[1]}"
  filename_version="${BASH_REMATCH[2]}"
  filename_run_id="${BASH_REMATCH[3]}"

  if [ "$(sed -n '1p' "$eval_file")" != "---" ]; then
    return 1
  fi
  frontmatter=$(awk 'NR==1 && $0=="---" {inside=1; next} inside && $0=="---" {found=1; exit} inside {print} END {if (!found) exit 1}' "$eval_file") || return 1
  frontmatter_lines=$(printf '%s\n' "$frontmatter" | wc -l)
  [ "$frontmatter_lines" -eq 7 ] || return 1

  [ "$(printf '%s\n' "$frontmatter" | grep -c '^target: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^target_blob: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^rubric_version: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^evaluator: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^evaluator_model: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^evaluated_at: ')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^run_id: ')" -eq 1 ] || return 1

  parsed_target=$(printf '%s\n' "$frontmatter" | sed -n -E 's/^target: "([^"]+)"$/\1/p')
  parsed_blob=$(printf '%s\n' "$frontmatter" | sed -n -E 's/^target_blob: "([0-9a-f]+)"$/\1/p')
  parsed_version=$(printf '%s\n' "$frontmatter" | sed -n -E 's/^rubric_version: ([0-9]+)$/\1/p')
  parsed_evaluated_at=$(printf '%s\n' "$frontmatter" | sed -n -E 's/^evaluated_at: "([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)"$/\1/p')
  parsed_run_id=$(printf '%s\n' "$frontmatter" | sed -n -E 's/^run_id: "([a-z0-9]{8,32})"$/\1/p')

  [ "$parsed_target" = "wiki/insight/pages/${expected_slug}.md" ] || return 1
  [[ "$parsed_blob" =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]] || return 1
  [[ "$parsed_version" =~ ^[0-9]+$ ]] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^evaluator: "codex"$')" -eq 1 ] || return 1
  [ "$(printf '%s\n' "$frontmatter" | grep -c '^evaluator_model: "gpt-5.6-sol"$')" -eq 1 ] || return 1
  [ -n "$parsed_evaluated_at" ] || return 1
  [ "$parsed_run_id" = "$filename_run_id" ] || return 1
  [ "$parsed_version" = "$filename_version" ] || return 1

  normalized_at="${parsed_evaluated_at//-/}"
  normalized_at="${normalized_at//:/}"
  [ "$normalized_at" = "$filename_timestamp" ] || return 1
  [ "$(date -u -d "$parsed_evaluated_at" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)" = "$parsed_evaluated_at" ] || return 1
  return 0
}

validate_evaluation_output() {
  local eval_file="$1"
  local expected_slug="$2"
  python3 "${script_dir}/evaluation_validator.py" "$eval_file" --slug "$expected_slug" >/dev/null 2>&1
}

for key in "${!col_slug_to_file[@]}"; do
  col="${key%%/*}"
  [[ "$col" != "insight" ]] && continue
  insight_slugs+=("${key##*/}")
done

if [ -z "$current_version" ]; then
  echo "WARN: ${rubric_file} に rubric_version: N が見つかりません。CHECK-9 をスキップします"
else
  for key in "${!col_slug_to_file[@]}"; do
    col="${key%%/*}"
    [[ "$col" != "insight" ]] && continue

    f="${col_slug_to_file[$key]}"
    slug="${key##*/}"
    insight_total=$((insight_total + 1))
    eval_dir="${evaluations_root}/${slug}"
    latest_eval=""
    latest_evaluated_at=""
    latest_run_id=""
    latest_version=""
    latest_blob=""
    metadata_invalid=0
    output_invalid=0

    if [ -d "$eval_dir" ]; then
      while IFS= read -r eval_file; do
        if ! validate_evaluation_metadata "$eval_file" "$slug"; then
          metadata_invalid=1
          invalid_metadata_history=$((invalid_metadata_history + 1))
          echo "EVALUATION_HISTORY_WARNING  collection=insight  slug=${slug}  reason=metadata  file=${eval_file}"
          continue
        fi
        if ! validate_evaluation_output "$eval_file" "$slug"; then
          output_invalid=1
          invalid_output_history=$((invalid_output_history + 1))
          echo "EVALUATION_HISTORY_WARNING  collection=insight  slug=${slug}  reason=output  file=${eval_file}"
          continue
        fi
        if [ -z "$latest_eval" ] \
          || [[ "$parsed_evaluated_at" > "$latest_evaluated_at" ]] \
          || { [ "$parsed_evaluated_at" = "$latest_evaluated_at" ] && [[ "$parsed_run_id" > "$latest_run_id" ]]; }; then
          latest_eval="$eval_file"
          latest_evaluated_at="$parsed_evaluated_at"
          latest_run_id="$parsed_run_id"
          latest_version="$parsed_version"
          latest_blob="$parsed_blob"
        fi
      done < <(find "$eval_dir" -maxdepth 1 -type f -name '*.md' -print | sort)
    fi

    if [ -z "$latest_eval" ]; then
      if [ "$output_invalid" -eq 1 ]; then
        echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=output  current_rubric=${current_version}"
        eval_output_invalid=$((eval_output_invalid + 1))
      elif [ "$metadata_invalid" -eq 1 ]; then
        echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=metadata  current_rubric=${current_version}"
        eval_malformed=$((eval_malformed + 1))
      else
        echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=missing  current_rubric=${current_version}"
        eval_missing=$((eval_missing + 1))
      fi
      continue
    fi

    current_blob=$(git hash-object "$f" 2>/dev/null) || true

    if [ -z "$current_blob" ]; then
      echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=metadata  latest=${latest_eval}  current_rubric=${current_version}"
      eval_malformed=$((eval_malformed + 1))
    elif [ "$latest_version" != "$current_version" ]; then
      echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=rubric  evaluated_rubric=${latest_version}  current_rubric=${current_version}  latest=${latest_eval}"
      eval_old_rubric=$((eval_old_rubric + 1))
    elif [ "$latest_blob" != "$current_blob" ]; then
      echo "EVALUATION_REQUIRED  collection=insight  slug=${slug}  reason=content  evaluated_blob=${latest_blob}  current_blob=${current_blob}  latest=${latest_eval}"
      eval_changed=$((eval_changed + 1))
    else
      echo "EVALUATION_CURRENT  collection=insight  slug=${slug}  rubric=${latest_version}  blob=${latest_blob}  evaluated_at=${latest_evaluated_at}  run_id=${latest_run_id}  latest=${latest_eval}"
      eval_current=$((eval_current + 1))
    fi
  done

  c9=$((eval_missing + eval_old_rubric + eval_changed + eval_malformed + eval_output_invalid))
  echo "EVALUATION_STATUS  rubric_version=${current_version}  total=${insight_total}  current=${eval_current}  missing=${eval_missing}  old_rubric=${eval_old_rubric}  content_changed=${eval_changed}  metadata_required=${eval_malformed}  output_required=${eval_output_invalid}  invalid_metadata_history=${invalid_metadata_history}  invalid_output_history=${invalid_output_history}  required=${c9}"

  if [ "$eval_old_rubric" -gt 0 ]; then
    echo "REEVALUATE_SCOPE  scope=all  reason=rubric_changed  count=${insight_total}"
  elif [ "$c9" -gt 0 ]; then
    echo "REEVALUATE_SCOPE  scope=required  reason=missing_or_content_changed  count=${c9}"
  else
    echo "REEVALUATE_SCOPE  scope=sample  reason=all_current  count=0"
  fi

  [ "$c9" -eq 0 ] && echo "OK: 全insight記事の評価が現行rubric・現行内容と一致"
  echo "COUNT: $c9"
fi
echo ""

# ── 品質ドリフト監査: 全評価が現行の場合のみランダムに3件 ────────────
echo "=== SAMPLE_EVALUATION: 品質ドリフト監査対象 ==="
if [ -z "$current_version" ] || [ ${#insight_slugs[@]} -eq 0 ]; then
  echo "INFO: サンプル評価対象なし"
elif [ "${c9:-1}" -gt 0 ]; then
  echo "INFO: 再評価対象があるためサンプル評価を省略"
else
  sample_n=3
  [ "${#insight_slugs[@]}" -lt "$sample_n" ] && sample_n=${#insight_slugs[@]}
  while IFS= read -r slug; do
    echo "SAMPLE_EVALUATION  collection=insight  slug=${slug}"
  done < <(printf '%s\n' "${insight_slugs[@]}" | shuf -n "$sample_n")
fi
echo ""

# ── suggestions/ のスキャン ──────────────────────────────────────────
echo "=== SUGGESTIONS: suggestions/ ディレクトリの未処理提案 ==="
csg=0

if [ -d "$suggestions_root" ]; then
  while IFS= read -r sf; do
    if [ "$(sed -n '1p' "$sf")" != "---" ]; then
      continue
    fi
    suggestion_meta=$(awk 'NR==1 && $0=="---" {inside=1; next} inside && $0=="---" {found=1; exit} inside {print} END {if (!found) exit 1}' "$sf") || continue
    status=$(printf '%s\n' "$suggestion_meta" | sed -n -E 's/^status:[[:space:]]*"?([a-z]+)"?$/\1/p')
    target=$(printf '%s\n' "$suggestion_meta" | sed -n -E 's/^target:[[:space:]]*"?([^"[:space:]][^"]*)"?$/\1/p')
    target="${target%\"}"
    if [ "$status" = "open" ] && [ -n "$target" ]; then
      echo "OPEN_SUGGESTION  file=${sf}  target=${target}"
      csg=$((csg + 1))
    fi
  done < <(find "$suggestions_root" -maxdepth 1 -name "*.md" ! -name ".gitkeep" | sort)
fi

[ "$csg" -eq 0 ] && echo "OK: 未処理suggestionなし"
echo "COUNT: $csg"
echo ""

# ── 完了 ─────────────────────────────────────────────────────────────
echo "=== DONE ==="
echo "NOTE: CHECK-4(重複概念)・CHECK-6(矛盾)・CHECK-7(合成機会) はLLM分析が必要"
echo "NOTE: CHECK-8 の候補はLLMが内容を確認し、削除前にユーザー確認を取ること"
echo "NOTE: CHECK-9 は evaluation-protocol.md に従い、同じlint実行内でCodex再評価・ランキング・改善キュー処理へ進む"
echo "NOTE: SAMPLE_EVALUATION はClaudeが採点せず、新しいCodex実行で品質ドリフトを確認する"
