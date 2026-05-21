#!/usr/bin/env bash
# .claude/skills/lint/lint-check.sh
#
# 構造的lintチェックを実行し、結果を標準出力に出力する。
# /lint スキルがこのスクリプトを先に実行し、出力をもとにLLM分析を行う。
#
# 担当するチェック:
#   CHECK-1: リンク切れ（完全自動）
#   CHECK-2: 孤立ページ（完全自動）
#   CHECK-3: リンク漏れ候補（誤検知あり → LLMが最終判断）
#   CHECK-5: 粒度メトリクス（数値計測のみ → LLMが最終判断）
#   CHECK-8: 低価値ページ候補（誤検知あり → LLMが最終判断）
#
# LLMが担当するチェック:
#   CHECK-4: 重複概念（意味的類似性）
#   CHECK-6: 矛盾（セマンティック推論）
#   CHECK-7: 未接続の合成機会
#
# 使い方: bash .claude/skills/lint/lint-check.sh [pages-dir]

set -uo pipefail

PAGES_DIR="${1:-wiki/pages}"

if [ ! -d "$PAGES_DIR" ]; then
  echo "ERROR: ページディレクトリが存在しません: $PAGES_DIR"
  exit 1
fi

mapfile -t page_files < <(find "$PAGES_DIR" -name "*.md" | sort)
total=${#page_files[@]}

echo "PAGES_TOTAL: $total"
echo ""

if [ "$total" -eq 0 ]; then
  echo "INFO: ページが存在しません。チェックをスキップします。"
  exit 0
fi

# ── スラグ・タイトルマップの構築 ─────────────────────────────────────
declare -A slug_to_title  # slug → title文字列

for f in "${page_files[@]}"; do
  slug=$(basename "$f" .md)
  title=$(grep -m1 '^title:' "$f" | sed 's/^title:[[:space:]]*//' | sed 's/["\x27]//g') || true
  slug_to_title["$slug"]="${title:-$slug}"
done

# ── CHECK-1: リンク切れ ───────────────────────────────────────────────
echo "=== CHECK-1: リンク切れ ==="
c1=0

for f in "${page_files[@]}"; do
  src=$(basename "$f" .md)
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    if [[ -z "${slug_to_title[$ref]+_}" ]]; then
      echo "BROKEN  src=${src}  ref=${ref}"
      c1=$((c1 + 1))
    fi
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null || true)
done

[ "$c1" -eq 0 ] && echo "OK: リンク切れなし"
echo "COUNT: $c1"
echo ""

# ── CHECK-2: 孤立ページ ──────────────────────────────────────────────
echo "=== CHECK-2: 孤立ページ ==="
declare -A referenced  # referenced[slug]=1 なら他ページからリンクされている

for f in "${page_files[@]}"; do
  while IFS= read -r link; do
    ref=$(echo "$link" | sed 's/\[\[//;s/\]\]//')
    referenced["$ref"]=1
  done < <(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null || true)
done

c2=0
for f in "${page_files[@]}"; do
  slug=$(basename "$f" .md)
  has_out=$(grep -c '\[\[[^]]*\]\]' "$f" 2>/dev/null) || has_out=0
  has_in=0
  [[ -n "${referenced[$slug]+_}" ]] && has_in=1

  if [[ "$has_out" -eq 0 && "$has_in" -eq 0 ]]; then
    echo "ORPHAN  slug=${slug}  title=${slug_to_title[$slug]}"
    c2=$((c2 + 1))
  fi
done

[ "$c2" -eq 0 ] && echo "OK: 孤立ページなし"
echo "COUNT: $c2"
echo ""

# ── CHECK-3: リンク漏れ候補 ──────────────────────────────────────────
# タイトルのテキストマッチは誤検知が発生しうる。LLMが内容を確認して判断する。
echo "=== CHECK-3: リンク漏れ候補 (誤検知の可能性あり - LLMで最終確認) ==="
c3=0

for src_f in "${page_files[@]}"; do
  src_slug=$(basename "$src_f" .md)
  # frontmatter（先頭の---〜---）を除いた本文のみ抽出
  body=$(awk 'BEGIN{f=0} /^---/{f++; next} f>=2{print}' "$src_f")

  for tgt_slug in "${!slug_to_title[@]}"; do
    [[ "$src_slug" == "$tgt_slug" ]] && continue
    tgt_title="${slug_to_title[$tgt_slug]}"

    # 4文字未満のタイトルは誤検知が多いためスキップ
    [[ ${#tgt_title} -lt 4 ]] && continue

    # タイトルが本文に登場 かつ [[tgt_slug]] リンクが存在しない
    if echo "$body" | grep -qF "$tgt_title" \
       && ! grep -q "\[\[${tgt_slug}\]\]" "$src_f"; then
      echo "MISSING_LINK  src=${src_slug}  mentions='${tgt_title}'  suggest=[[${tgt_slug}]]"
      c3=$((c3 + 1))
    fi
  done
done

[ "$c3" -eq 0 ] && echo "OK: リンク漏れ候補なし"
echo "COUNT: $c3"
echo ""

# ── CHECK-5: 粒度メトリクス ──────────────────────────────────────────
# 数値のみ計測。分割/統合の要否はLLMが本文を読んで判断する。
#   LARGE  : 総文字数 > 3000 （広すぎる可能性）
#   TINY   : 総文字数 < 150  （狭すぎる可能性）
#   MANY_LINKS: [[リンク]] 数 > 10 （広すぎる可能性）
echo "=== CHECK-5: 粒度メトリクス (最終判断はLLMが行う) ==="
c5=0

for f in "${page_files[@]}"; do
  slug=$(basename "$f" .md)
  chars=$(wc -m < "$f")
  links=$(grep -oh '\[\[[^]]*\]\]' "$f" 2>/dev/null | wc -l) || links=0
  sections=$(grep -c '^## ' "$f" 2>/dev/null) || sections=0
  flags=""
  [[ "$chars" -gt 3000 ]] && flags="${flags} LARGE(${chars}chars)"
  [[ "$chars" -lt 150 ]]  && flags="${flags} TINY(${chars}chars)"
  [[ "$links" -gt 10 ]]   && flags="${flags} MANY_LINKS(${links})"

  if [[ -n "$flags" ]]; then
    echo "METRICS  slug=${slug}  chars=${chars}  links=${links}  sections=${sections}  flags=${flags}"
    c5=$((c5 + 1))
  fi
done

[ "$c5" -eq 0 ] && echo "OK: メトリクス異常なし"
echo "COUNT: $c5"
echo ""

# ── CHECK-8: 低価値ページ候補 ────────────────────────────────────────
# referenced マップは CHECK-2 で構築済み。
#   TINY_ORPHAN : 150字未満 かつ 被参照ゼロ・発リンクゼロ
#   REDIRECT    : 本文（frontmatter除去後）が100字未満 かつ → [[slug]] パターンのみ
echo "=== CHECK-8: 低価値ページ候補 (最終判断はLLMが行う) ==="
c8=0

for f in "${page_files[@]}"; do
  slug=$(basename "$f" .md)
  chars=$(wc -m < "$f")
  has_out=$(grep -c '\[\[[^]]*\]\]' "$f" 2>/dev/null) || has_out=0
  has_in=0
  [[ -n "${referenced[$slug]+_}" ]] && has_in=1

  if [[ "$chars" -lt 150 && "$has_out" -eq 0 && "$has_in" -eq 0 ]]; then
    echo "LOW_VALUE  slug=${slug}  reason=TINY_ORPHAN  chars=${chars}"
    c8=$((c8 + 1))
    continue
  fi

  body=$(awk 'BEGIN{f=0} /^---/{f++; next} f>=2{print}' "$f")
  body_chars=$(echo "$body" | wc -m)
  if [[ "$body_chars" -lt 100 ]] && echo "$body" | grep -q '→.*\[\['; then
    echo "LOW_VALUE  slug=${slug}  reason=REDIRECT  body_chars=${body_chars}"
    c8=$((c8 + 1))
  fi
done

[ "$c8" -eq 0 ] && echo "OK: 低価値ページ候補なし"
echo "COUNT: $c8"
echo ""

# ── 完了 ─────────────────────────────────────────────────────────────
echo "=== DONE ==="
echo "NOTE: CHECK-4(重複概念)・CHECK-6(矛盾)・CHECK-7(合成機会) はLLM分析が必要"
echo "NOTE: CHECK-8 の候補はLLMが内容を確認し、削除前にユーザー確認を取ること"
