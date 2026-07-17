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
#   CHECK-9: 再審査待ち（insightコレクションのみ。reviewedバージョン照合）
#
# LLMが担当するチェック:
#   CHECK-4: 重複概念（意味的類似性）
#   CHECK-6: 矛盾（セマンティック推論）
#   CHECK-7: 未接続の合成機会
#
# 補助出力:
#   SAMPLE: 本質サンプリング監査用にランダムに3ページ選出（insightコレクションのみ）
#   OPEN_SUGGESTION: suggestion/ 配下で status: open の提案ファイル
#
# 使い方:
#   bash lint-check.sh --collection name:path [--collection name2:path2 ...]
#
# 例:
#   bash .claude/skills/lint/lint-check.sh \
#     --collection insight:wiki/insight/pages \
#     --collection it:wiki/it/pages

set -uo pipefail

# ── 引数パース ────────────────────────────────────────────────────────
declare -A collection_paths  # collection_paths[name]=path
declare -a collection_names  # 順序保持用

while [[ $# -gt 0 ]]; do
  case "$1" in
    --collection)
      IFS=':' read -r col_name col_path <<< "$2"
      collection_paths["$col_name"]="$col_path"
      collection_names+=("$col_name")
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

# ── CHECK-9: 再審査待ち（insightコレクションのみ） ──────────────────
echo "=== CHECK-9: 再審査待ち (insightコレクションのみ) ==="
c9=0

criteria_file="wiki/insight/references/essence-review-criteria.md"
current_version=""
if [ -f "$criteria_file" ]; then
  current_version=$(grep -m1 -oE 'version:[[:space:]]*[0-9]+' "$criteria_file" | grep -oE '[0-9]+') || true
fi

if [ -z "$current_version" ]; then
  echo "WARN: ${criteria_file} に version: N が見つかりません。CHECK-9 をスキップします"
else
  for key in "${!col_slug_to_file[@]}"; do
    col="${key%%/*}"
    [[ "$col" != "insight" ]] && continue
    f="${col_slug_to_file[$key]}"
    slug="${key##*/}"
    reviewed=$(grep -m1 -oE '^reviewed:[[:space:]]*[0-9]+' "$f" | grep -oE '[0-9]+') || true

    if [ -z "$reviewed" ]; then
      echo "STALE_REVIEW  collection=${col}  slug=${slug}  reviewed=none  current=${current_version}"
      c9=$((c9 + 1))
    elif [ "$reviewed" -lt "$current_version" ]; then
      echo "STALE_REVIEW  collection=${col}  slug=${slug}  reviewed=${reviewed}  current=${current_version}"
      c9=$((c9 + 1))
    fi
  done

  [ "$c9" -eq 0 ] && echo "OK: 再審査待ちなし"
fi
echo "COUNT: $c9"
echo ""

# ── 本質サンプリング監査: ランダムに3ページ選出（insightコレクションのみ） ──
echo "=== SAMPLE: 本質サンプリング監査対象 ==="
declare -a insight_slugs
for key in "${!col_slug_to_file[@]}"; do
  col="${key%%/*}"
  [[ "$col" != "insight" ]] && continue
  insight_slugs+=("${key##*/}")
done

if [ ${#insight_slugs[@]} -eq 0 ]; then
  echo "INFO: insightコレクションにページがありません"
else
  sample_n=3
  [ "${#insight_slugs[@]}" -lt "$sample_n" ] && sample_n=${#insight_slugs[@]}
  while IFS= read -r slug; do
    echo "SAMPLE  collection=insight  slug=${slug}"
  done < <(printf '%s\n' "${insight_slugs[@]}" | shuf -n "$sample_n")
fi
echo ""

# ── suggestion/ のスキャン ───────────────────────────────────────────
echo "=== SUGGESTIONS: suggestion/ ディレクトリの未処理提案 ==="
csg=0

if [ -d "suggestion" ]; then
  while IFS= read -r sf; do
    status=$(grep -m1 -oE '^status:[[:space:]]*[a-z]+' "$sf" | sed 's/^status:[[:space:]]*//') || true
    if [[ -z "$status" || "$status" == "open" ]]; then
      target=$(grep -m1 -oE '^target:[[:space:]]*.*' "$sf" | sed 's/^target:[[:space:]]*//' | sed 's/["\x27]//g') || true
      echo "OPEN_SUGGESTION  file=${sf}  target=${target:-unknown}"
      csg=$((csg + 1))
    fi
  done < <(find "suggestion" -maxdepth 1 -name "*.md" ! -name ".gitkeep" | sort)
fi

[ "$csg" -eq 0 ] && echo "OK: 未処理suggestionなし"
echo "COUNT: $csg"
echo ""

# ── 完了 ─────────────────────────────────────────────────────────────
echo "=== DONE ==="
echo "NOTE: CHECK-4(重複概念)・CHECK-6(矛盾)・CHECK-7(合成機会) はLLM分析が必要"
echo "NOTE: CHECK-8 の候補はLLMが内容を確認し、削除前にユーザー確認を取ること"
echo "NOTE: CHECK-9 の再審査自体はバックフィル運用で行う（lintは検出と件数報告のみ）"
echo "NOTE: SAMPLE のページは essence-review-criteria.md のC1〜C3でLLMが再判定する"
