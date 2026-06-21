---
status: open
target: [availability-heuristic, framing-effect, planning-fallacy, peak-end-rule, prospect-theory]
created: "2026-05-30"
---

# 提案: 認知バイアス系ページに「対処・補正」セクションを追加する

## 対象

- `wiki/insight/pages/availability-heuristic.md`
- `wiki/insight/pages/framing-effect.md`
- `wiki/insight/pages/planning-fallacy.md`
- `wiki/insight/pages/peak-end-rule.md`
- `wiki/insight/pages/prospect-theory.md`

## 判定

不合格。認知バイアス・ヒューリスティックを扱っているが、`schema.md` が必須化している対処・補正セクションがない。

## 根拠

`wiki/insight/schema.md` は「認知バイアス・ヒューリスティック・心理メカニズムを扱うページは『対処・補正』セクションを必須」としている。上記ページは人間の認知歪みを扱うため対象に該当する。

## 改善案

各ページに `## 対処` または `## 補正` を追加し、単なる実践Tipsではなく「核心のどこに干渉するか」を明記する。

- `availability-heuristic`: 想起容易性ではなくベースレート・統計・外部データに戻す。
- `framing-effect`: 同じ選択肢を利益フレームと損失フレームの両方で言い換え、参照点依存を露出させる。
- `planning-fallacy`: 内部視点から外部視点へ切り替え、類似プロジェクトの実績分布を参照する。
- `peak-end-rule`: 体験設計ではピークと終わりを意図的に設計し、評価時は総量・頻度・継続時間の記録を併用する。
- `prospect-theory`: 参照点を明示し、損失/利益の表現を反転させても同じ判断になるか検査する。
