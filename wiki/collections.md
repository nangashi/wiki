# コレクション定義

`/ingest`・`/query`・`/lint` スキルはこのファイルを読んでコレクション構成を把握する。
新しいコレクションを追加するときはここに定義を追記する。

---

## コレクション一覧

### insight
- **path**: `wiki/insight/`
- **schema**: `wiki/insight/schema.md`
- **index**: `wiki/insight/index.md`
- **再利用性審査**: `wiki/insight/references/reusability-criteria.md`
- **記事品質基準**: `wiki/insight/references/article-quality-rubric.md`
- **評価・改善手順**: `wiki/insight/references/evaluation-protocol.md`
- **説明**: 再利用可能な推論モデル。事象を説明する因果・構造を持ち、それを使って元のソースにないケースの予測・診断・判断ができる原則・洞察・メンタルモデル
- **判定目安**: 特定事例を離れて再利用できる因果・構造を持ち、未知ケースの推論に使える知識。詳細な採用判定は `wiki/insight/references/reusability-criteria.md` を正本とする

### it
- **path**: `wiki/it/`
- **schema**: `wiki/it/schema.md`
- **index**: `wiki/it/index.md`
- **説明**: 技術単位のリファレンス集（1技術1ページ）。技術の全体像・採用判断・アンチパターン・トレードオフを集約し、記事として読める体系的理解に使う。個別の実装事例・インシデントは原則リファレンスページに統合する
- **判定目安**: 特定技術に紐づき、体系的理解・採用判断・実装・運用知見に寄与する知識。詳細な採用基準は `wiki/it/schema.md` を正本とする

---

## コレクション間リンク記法

| リンク | 意味 |
|--------|------|
| `[[slug]]` | 同一コレクション内のページ |
| `[[insight:slug]]` | insight コレクションのページへの参照 |
| `[[it:slug]]` | it コレクションのページへの参照 |

スラグはすべてのコレクションを横断してユニークであること。
