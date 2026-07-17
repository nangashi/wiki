---
status: applied
target: motivational-questioning
created: "2026-05-30"
---

# 提案: [[motivational-questioning]] のリンク切れを修正する

## 対象

- `wiki/insight/pages/motivational-questioning.md`

## 判定

不合格。存在しない `[[instruction-depth]]` へのリンクがある。

## 根拠

lint 実行結果で `BROKEN collection=insight src=motivational-questioning ref=instruction-depth type=local` が検出された。`wiki/insight/pages/instruction-depth.md` は存在しない。

## 改善案

次のどちらかを行う。

1. `instruction-depth` が insight の概念として独立するなら、`wiki/insight/pages/instruction-depth.md` を作成する。
2. 既存の IT 文書や別概念を指す意図なら、リンクを正しい slug に修正する。

現状の説明は「人への指示の4層構造（目的→業務→要件→参考）」であり、独立した insight 概念として成立する可能性がある。ただし、本文が単なる手順整理に留まるなら、`motivational-questioning` の関連から削除する方がよい。
