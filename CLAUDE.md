## 行動方針

### 全体
- 忖度しない: ページ品質・スキル実行判断・提案で問題があれば率直に指摘する

### insightコレクション
- 本質を最優先: 「この概念の核心は何か」を繰り返し自問し、答えが出てから書く
- 有用な情報に絞る: 本質と無関係な説明・具体例は含めない

## 外部協調（Muse）

- スキル定義は `.claude/skills/` のみに置く。**`.agents/` ディレクトリを作らないこと** — 二重管理で乖離する
- 調査・監査・ファクトチェックは外部の監督エージェント Muse が担う（別系統モデル）。Muse は Claude Code を起動して作業させ、差分をレビューする。リポジトリ内で `codex exec` は使わない（OpenAI 契約終了のため廃止）
- 取り込みの協調フロー:
  1. Muse が一次資料を調査し、ブリーフを `.tmp/briefs/<YYYY-MM-DD>-<topic-slug>.md` に置く（様式の正本は `.claude/skills/ingest/brief-template.md`。核心文と骨格までで、本文案は書かない）
  2. Claude Code が `/ingest` のブリーフ入力モードで執筆する（モデルは Opus）
  3. Muse が原典を再取得して草稿をファクトチェックする（ブリーフとの照合で済ませない）
  4. 指摘の修正は1往復まで。残った指摘は queue の proposal に落とす
- **独立調査の封**: 深掘りレビューでは、Muse は対象ページ本文を読む前に、タイトルと概要だけから独立調査メモを作る。それを書く前にページ本文や Claude Code のレビュー結果を見ない
- **提案者と承認者の分離**: Muse の監査・調査に由来する指摘は必ず queue の proposal から始める。`auto: true` への変換は、ユーザーの承認（`/lint` ステップ4、またはチャットでの明示承認）後だけ。Muse が自分の指摘を auto 化しない
- 執筆（ingest でのページ作成・更新）は Opus で行う。Muse が起動する場合は `--model opus` を付け、スキル側も frontmatter で指定する
- Muse が駆動する ingest は専用ブランチ（`ingest/<topic-slug>`）で作業し、Muse が差分をレビューしてから main にマージする。通常の対話セッションでの `/ingest` は現行どおりでよい
- `AGENTS.md` は `CLAUDE.md` へのsymlink。他のエージェントにも同じ行動方針を適用するためのもの

## メンテナンス体制

- ページ修正は `queue/` に1件1ファイルで登録する（形式・ステータス・ルールは `queue/README.md` が正本）。`TODO.md` や `suggestions/` は作らない
  - `kind: replace`（`old` が対象ページにちょうど1回出現する固定文字列置換）と `kind: proposal`（人間の判断が要るもの）に分ける
  - 削除・統合・分割は常に proposal。replace 1件が触れるのは1ページのみ
- `/dream` が夜間に `dream/auto` ブランチで実行される: auto replace を最大2件適用、本質サンプル再判定、再審査バックフィル最大2ページ。main には直接書き込まない
- `dream/auto` は週1回Museがレビューして main にマージする
- **`auto: true` の項目を作れるのはユーザー本人か、ユーザーが承認したセッションのみ。Muse の指摘に由来する項目は、ユーザーの承認前に auto 化しない。** `/dream` は auto 項目を作らず、proposal を適用しない
- proposal の承認・却下は `/lint` のステップ4で行う。未処理 proposal は20件が上限（上限中は `/dream` が新規登録しない）
