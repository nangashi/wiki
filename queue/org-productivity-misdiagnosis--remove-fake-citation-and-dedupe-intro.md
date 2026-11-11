---
id: org-productivity-misdiagnosis--remove-fake-citation-and-dedupe-intro
target: org-productivity-misdiagnosis
kind: proposal
auto: false
status: proposed
source: both P1
---

**org-productivity-misdiagnosis** — 実在しない学術的裏づけ＋冒頭の重複

- `org-productivity-misdiagnosis.md:34` 「5分の依頼が実際には50分の中断コストを発生させる（認知科学）」→ sourcesはサイボウズ式の記事1件のみで、この数値に対応する研究がない。「（認知科学）」の括弧書きが実在しない裏づけを装っている（俗説「復帰に23分15秒」に隣接する）。数値と括弧書きを外し、`[[interruption-recovery-cost]]` へのリンクで根拠を担保する。
  - 監査2の修正案文言: 「短い依頼でも、作業の切替と元の課題への復帰によって、依頼時間を大きく超える中断コストが生じることがある」
- `org-productivity-misdiagnosis.md:14,20` 冒頭で `proxy-metrics-knowledge-work` の代理指標の説明をほぼ再掲している → 重複説明を削り `[[proxy-metrics-knowledge-work]]` へのリンクで済ませ、独自部分（個人への誤帰属、5類型）に紙幅を集中する。※完全統合は不要（核心が「誤帰属」vs「指標の歪み」で別）。
- 出典: 監査2 A5、監査1 中優先度

proposal にした理由: 複数箇所の編集を含み、冒頭の重複削減は編集判断を要する。
