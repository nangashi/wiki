---
status: applied
target: [cialdini-persuasion-triggers, reciprocity-principle, commitment-and-consistency, social-proof, liking-principle, authority-principle, scarcity-principle]
created: "2026-05-30"
---

# 提案: [[cialdini-persuasion-triggers]] と個別原則ページの役割境界を明確にする

## 対象

- `wiki/insight/pages/cialdini-persuasion-triggers.md`
- `wiki/insight/pages/reciprocity-principle.md`
- `wiki/insight/pages/commitment-and-consistency.md`
- `wiki/insight/pages/social-proof.md`
- `wiki/insight/pages/liking-principle.md`
- `wiki/insight/pages/authority-principle.md`
- `wiki/insight/pages/scarcity-principle.md`

## 判定

統合設計は妥当だが、上位ページと個別ページの境界がやや曖昧。

## 根拠

`cialdini-persuasion-triggers` は上位概念として「固定的行動パターンがトリガーで自動起動する」という共通原理を持っており、独立価値がある。一方、個別ページにも同じ「認知資源節約のショートカット」「自動反応」という説明が繰り返されている。

このままだと、上位ページは索引、個別ページは重複説明になりやすい。

## 改善案

上位ページと個別ページの責務を分ける。

- 上位ページ: 共通原理、7原則の分類根拠、横断的な防御原則だけを書く。
- 個別ページ: その原則固有の心理メカニズム、成立条件、悪用パターン、対処を書く。

個別ページの冒頭では共通原理の説明を短くし、`cialdini-persuasion-triggers` へ寄せる。代わりに各原則固有の非自明なメカニズムを厚くする。
