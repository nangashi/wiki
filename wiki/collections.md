# コレクション定義

`/ingest`・`/query`・`/lint` スキルはこのファイルを読んでコレクション定義を把握する。
このwikiは insight コレクションのみで構成する。

---

## insight
- **path**: `wiki/insight/`
- **schema**: `wiki/insight/schema.md`
- **index**: `wiki/insight/index.md`
- **再利用性審査**: `wiki/insight/references/reusability-criteria.md`
- **説明**: 再利用可能な推論モデル。事象を説明する因果・構造を持ち、それを使って元のソースにないケースの予測・診断・判断ができる原則・洞察・メンタルモデル
- **判定目安**: 特定事例を離れて再利用できる因果・構造を持ち、未知ケースの推論に使える知識。詳細な採用判定は `wiki/insight/references/reusability-criteria.md` を正本とする

---

## リンク記法

ページ間リンクは `[[slug]]` で書く。スラグはwiki全体でユニークであること。
