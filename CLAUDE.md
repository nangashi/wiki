## 行動方針

### 全体
- 忖度しない: ページ品質・スキル実行判断・提案で問題があれば率直に指摘する

### insightコレクション
- 本質を最優先: 「この概念の核心は何か」を繰り返し自問し、答えが出てから書く
- 有用な情報に絞る: 本質と無関係な説明・具体例は含めない

## リポジトリ構成の注意

- Codexは `codex exec` を **本体のBashツールから `run_in_background: true` で直接実行** する。`/codex:rescue`・`codex:codex-rescue` サブエージェント・`codex-companion.mjs` は使わない
  ```bash
  codex exec -C "$(git rev-parse --show-toplevel)" -s read-only \
    -o <出力先.md> "$(cat <プロンプト.md>)" < /dev/null > <ログ.log> 2>&1
  ```
  - **サブエージェント経由は不可**（実測）: Bashが120秒でバックグラウンド送りにした直後にサブエージェントがターンを終え、Codexのプロセスツリーごと破棄される。`run_in_background: true` を付けても防げない
  - **`< /dev/null` は必須**（実測）: 省くとCodexがstdin待ちで無限ハングする
  - **プロンプトは `Write` ツールでファイルに書く**: シェルのクォート崩れを避ける（ヒアドキュメントも使わない）
  - **結果は `-o` のファイルから読む**: stdoutを取り逃しても残る
  - Codexに書き込みをさせる場合のみ `-s workspace-write`
- スキル定義は `.claude/skills/` のみに置く（Claude Code専用）。**`.agents/` ディレクトリを作らないこと** — 二重管理で乖離し、Codexが古いスキル定義を自律的に読み込んで動く事故が起きた
- Codexは「調査・レビュー担当」であり、このリポジトリのスキルを実行する主体ではない。Codexに渡すプロンプトは、必要な基準・文脈をすべて埋め込んだ自己完結型にすること（`.claude/skills/` を参照させない）
- `AGENTS.md` は `CLAUDE.md` へのsymlink。Codexにもこの行動方針を継承させるためのもの

## メンテナンス体制

- ページ修正は `queue/` に1件1ファイルで登録する（形式・ステータス・ルールは `queue/README.md` が正本）。`TODO.md` や `suggestions/` は作らない
  - `kind: replace`（`old` が対象ページにちょうど1回出現する固定文字列置換）と `kind: proposal`（人間の判断が要るもの）に分ける
  - 削除・統合・分割は常に proposal。replace 1件が触れるのは1ページのみ
- `/dream` が夜間に `dream/auto` ブランチで実行される: auto replace を最大2件適用、本質サンプル再判定、再審査バックフィル最大2ページ。main には直接書き込まない
- `dream/auto` は週1回Museがレビューして main にマージする
- **`auto: true` の項目を作れるのはユーザー本人かMuseが監督するセッションのみ。** `/dream` は auto 項目を作らず、proposal を適用しない
- proposal の承認・却下は `/lint` のステップ4で行う。未処理 proposal は20件が上限（上限中は `/dream` が新規登録しない）
