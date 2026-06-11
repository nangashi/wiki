# 提案: [[unlearn]] の関連リンク密度を下げる

## 対象

- `wiki/insight/pages/unlearn.md`

## 判定

要整理。関連リンクが多く、ページの核心に対して関係の強弱が混在している。

## 根拠

lint の粒度メトリクスで `MANY_LINKS(11)` が検出された。本文自体は「成功体験が前提を無意識化し検証回路を閉ざす」という核心があり、品質は低くない。しかし関連セクションが広がりすぎて、読者が次にどの概念へ進むべきか判断しにくい。

`schema.md` の関連セクションは「この概念との関係を1行で説明」する場であり、網羅的タグリストではない。

## 改善案

関連リンクを「直接関係」と「二次関係」に分け、直接関係だけを残す。

直接関係候補:

- `exit-criteria-first`
- `decision-structure`
- `identity-foreclosure`
- `four-thinking-modes`
- `growth-vs-fixed-mindset`

`depth-creates-breadth`、`character-ethics-vs-personality-ethics`、`stimulus-response-freedom` などは本文内リンクまたは削除候補にする。
