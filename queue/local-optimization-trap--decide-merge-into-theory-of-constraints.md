---
id: local-optimization-trap--decide-merge-into-theory-of-constraints
target: local-optimization-trap
kind: proposal
auto: false
status: proposed
source: audit-2026-08-01 P3
---

**local-optimization-trap → theory-of-constraints への統合判断（要ユーザー確認）**

- 核心文（`local-optimization-trap.md:17`）がTOCの核心とほぼ重複。「非ボトルネック高稼働が害になる理由」の節もTOCの「非制約のアイドルは設計上正しい」と重複。
- 統合案: ハービーのハイキング、依存的事象＋統計的変動という「なぜ」の導出、組織・開発への適用例を `theory-of-constraints` の該当節へ移植し、本ページは削除。
- **削除を伴う破壊的変更なので、移植する節を取捨選択した統合案を先に提示してから実行する**（review-page skill R5）。統合後にTOCページが冗長にならないことが条件。
- ※ このページ単独の過剰主張修正（P2相当、「非制約で節約した1時間は何の価値も生まない」型）は、統合するなら無駄になるので統合判断の後に回す。
- 出典: 監査1 中優先度
