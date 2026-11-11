---
id: productivity-layer-model--verify-numbers-against-primary-source
target: productivity-layer-model
kind: proposal
auto: false
status: proposed
source: both P3
---

**productivity-layer-model** — 数値の一次資料照合（**調査タスク**）

- `productivity-layer-model.md:37-38` 「体感 約+20%」vs「デリバリー安定性は負の相関 約−19%」→ sourcesがSpeaker Deck 1件で、母集団・指標・測定期間が追えない。監査1のCodex調査では2024年DORA公式レポートの値は −7.2%（AI採用25%増シナリオ）で一致しない。
- また「体感」と「実態データ」が同一対象・同一尺度か不明なまま、この2数値の対比から6層モデルの因果（L3の調整コストが原因）を導いている。
- **手順**: (1) 出典スライドを再確認して算出根拠を特定 → (2) 追えなければ数値を「紹介元資料では〜という事例が示されている」に格下げ → (3) 因果は「個人作業の改善が調整工程で吸収されている可能性を示すが、測定差や品質変化など他の説明も検討が必要」と留保。
- ※ −19%がスライド独自のアンケート集計に基づく可能性もあり、DORA公式値への単純差し替えは正しいとは限らない。一次資料の確認が先。
- 出典: 監査2 A8、監査1 高優先度
