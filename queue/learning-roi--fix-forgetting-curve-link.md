---
id: learning-roi--fix-forgetting-curve-link
target: learning-roi
kind: replace
auto: true
status: applied
applied: 2026-11-13
source: audit-2026-08-01 P1
old: "（実験の詳細と俗説「1日後に74%忘れる」への注意は [[testing-effect]]）"
new: "（実験の詳細と俗説「1日後に74%忘れる」への注意は [[forgetting-curve]]）"
---

**learning-roi** — リンク誤記

- `learning-roi.md:20` 俗説「1日後に74%忘れる」への注意の参照先が `[[testing-effect]]` になっているが、該当記述は `forgetting-curve.md:21` にある。`[[forgetting-curve]]` に修正。**（機械的、即対応可）**
- 出典: 監査1 高優先度

※ 同ページの他の `[[testing-effect]]`（:39, :46）は正しい参照なので変更しない。元タスクのソース不足の指摘は `learning-roi--strengthen-sources` に分離した。
