---
status: applied
target: [reciprocity-principle, commitment-and-consistency, social-proof, liking-principle, authority-principle, scarcity-principle]
created: "2026-05-30"
---

# 提案: チャルディーニ個別原則ページに防御・対処を追加する

## 対象

- `wiki/insight/pages/reciprocity-principle.md`
- `wiki/insight/pages/commitment-and-consistency.md`
- `wiki/insight/pages/social-proof.md`
- `wiki/insight/pages/liking-principle.md`
- `wiki/insight/pages/authority-principle.md`
- `wiki/insight/pages/scarcity-principle.md`

## 判定

部分不合格。核心と事例はあるが、承諾誘導への防御が独立セクションとして整理されていない。

## 根拠

これらは「説得の自動トリガー」という心理メカニズムを扱うページであり、`schema.md` の認知・行動メカニズム系の実用条件に照らすと、意思決定への影響と補正方法がセットで必要になる。`authority-principle` には「利害関係の確認」が本文中にあるが、対処セクションとして明示されていないため、同種ページ間の形式も揃っていない。

## 改善案

各ページに `## 対処` を追加し、`cialdini-persuasion-triggers.md` の「防御の原則」を個別メカニズムに展開する。

- 返報性: 受け取ったものと要求の妥当性を切り離して評価する。
- 一貫性: 過去の発言でなく現在の証拠に基づき再選択する。
- 社会的証明: 「似た他者」の行動が本当に同じ条件下の情報か確認する。
- 好意: 人物への好意と提案内容の評価を分離する。
- 権威: 専門領域と利害関係を確認する。
- 希少性: 入手困難性と実質価値を分離し、時間制約を外しても欲しいか問う。
