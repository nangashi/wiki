---
name: ingest
description: 指定したソースから調査・作成・Codex評価・改善・再評価まで行いwikiへ取り込む
---

# /ingest スキル

新規作成と既存ページへの追記の唯一の入口。利用者へ評価モードやCodex利用の有無を選ばせず、ソースと検証リスクから必要な処理を自動判断する。

## 事前準備とコレクション判定

1. `wiki/collections.md` を読み、コレクション構成と判定ルールを確認する。
2. ソースのURL・タイトル・概要をもとに `insight` / `it` の該当可否と理由を示し、追加先をユーザーに確認する。
3. 承認されたコレクションの `schema.md` を全文読む。
4. insightなら `reusability-criteria.md`、`article-quality-rubric.md`、`japanese-style-guide.md`、`evaluation-protocol.md` を全文読む。

```text
コレクション判定
- insight: YES / NO / 候補 — 理由
- it: YES / NO / 候補 — 理由
→ 判定コレクションに追加しますか？
```

## ソース種別

| 入力 | 種別 | 基本処理 |
|---|---|---|
| `http://...` / `https://...` | Web | 本文取得、主要概念と外部ソース候補を抽出 |
| `.pdf` | PDF | PDFを読み、ファイル名と確認した主張を外部ソースへ記録 |
| `本:` / `book:` | 書籍 | 著者・出版社・原典を優先して5〜8回検索 |
| `トピック:` / `topic:` | トピック | 定義、原論文、代表例、限界を5〜8回検索 |

複数入力は順に処理する。Web・書籍・トピックは一次資料を優先し、一次／二次／三次を区別する。insightで一次・二次ソースを確保できない候補は作成せず保留する。

## insightの処理

### 1. 採用・重複判定

- `reusability-criteria.md` のR1〜R4を適用する。必須ゲートを通らない候補は記事化しない。
- `wiki/insight/index.md` と既存ページを確認し、新規ページより既存ページへの追記を優先する。
- 特定言語・ツールを外しても残る構造だけをinsight候補にする。固有実装は必要最小限の具体例へ置く。
- 関係概念、統合、元ページ削除の判断は `schema.md` に従う。削除・統合・リダイレクト化はユーザー確認なしに行わない。

### 2. 独立調査の自動判断

書籍・トピック・外部Webから新規記事を作る場合は、原則としてCodexによる独立調査を行う。十分な一次資料を直接与えられ、主要主張がその資料内で追跡できる場合は作成前の独立調査を省略できるが、作成後評価は省略しない。

独立調査が必要なら、Claude CodeのWriteツールで自己完結プロンプトを `/tmp` に作り、本体Bashから `run_in_background: true` でCodexを直接起動する。モデルはSolを使う。

```bash
codex exec -C "$(git rev-parse --show-toplevel)" -s read-only \
  -m gpt-5.6-sol \
  -o /tmp/codex-ingest-research-out.md \
  "$(cat /tmp/codex-ingest-research-prompt.md)" \
  < /dev/null > /tmp/codex-ingest-research.log 2>&1
```

プロンプトには入力内容、調査目的、一次資料優先、核心候補と根拠、未確認事項、URLつき出力形式を埋め込む。Codexへリポジトリのスキルを参照させず、記事を書かせない。Claude Codeが調査結果を吟味して執筆する。

### 3. 草稿作成

- `schema.md` の共通書き込み手順と本文形式に従う。
- `article-quality-rubric.md` と `japanese-style-guide.md` を執筆基準として使うが、Claude Code自身は採点しない。
- 新規ページは一時的に作成してよいが、`wiki/insight/index.md` の新規項目は品質ループ完了後に確定する。
- 既存ページの実質的な変更では `updated` と末尾の外部ソースを更新する。新規frontmatterへ `sources`や`reviewed`を追加しない。
- 本文、関連リンク、逆リンク、外部ソースを先に確定する。変更した逆リンク先を含む全insightページを評価対象にし、共通source validatorで形式を確認する。

### 4. Codex評価・Claude改善・独立再評価

`evaluation-protocol.md` を省略せず実行する。

1. 草稿、関連リンク、逆リンク、外部ソースを確定し、`insight_source_validator.py`で形式確認する。新規記事はcategoryを問わず診断が1件でもあれば、`pages/`への正式配置・評価済み扱い・index追加へ進まない。要確認・外部ソース未確認を残さない。
2. Codex（Sol）が共通ルーブリックで評価し、評価履歴を `evaluations/insight/<slug>/` に保存する。
3. `要外部調査: はい` または同プロトコルのリスク条件があれば、別のCodex実行で外部検証する。
4. 不合格ならClaude CodeがBlocking、Major、最低観点から1〜3項目を改善する。
5. 前回点数を渡さない新しいCodex実行で再評価する。
6. 合格または停止条件まで最大3回繰り返す。

各Codex出力は保存前に`evaluation_validator.py`へ渡す。不正なら保存せず、エラーや前回出力を加えない同一のクリーンプロンプトでretryする。Codexはread-onlyで評価し、記事を変更しない。Claude CodeはCodexの点数を補完・代行しない。最終評価後は記事blobを変えず、変更が必要なら再評価する。全変更ページの最終評価後にindexだけを最後に更新する。最大回数で未達停止した新規記事は未公開の草稿としてindexへ追加せず、残課題を報告する。

## itの処理

itは `wiki/it/schema.md` の共通書き込み手順に従う。今回のinsight用点数評価は適用しない。新規ページを乱立させず、1技術1ページへの集約、採用判断、アンチパターン、トレードオフを優先する。

## 完了報告

- 入力ソースと自動実行した調査
- コレクションごとの新規・更新・スキップ
- insight再利用性ゲートの結果
- 初回／最終のraw_score、score_cap、final_score、品質区分、Blocking/Major、観点別傾向
- 外部検証で修正・留保した主張
- 追加した相互リンクとindex更新
- 停止時の残課題
- insightを変更した場合の `/anki` 案内
