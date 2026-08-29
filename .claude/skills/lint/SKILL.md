---
name: lint
description: wiki全体の構造監査と、rubric更新時のinsight再評価・改善キュー処理を行う
---

# /lint スキル

wiki全体のリンク、孤立、重複、粒度、矛盾、低価値候補を監査する。さらにinsight評価履歴を現行rubricと自動照合し、必要なら同じ実行内でCodex再評価、ランキング、改善キュー処理まで進む。動作切替オプションは設けない。

## 事前準備

1. `wiki/collections.md` と各コレクションの `schema.md` を読む。
2. insightについて `article-quality-rubric.md`、`japanese-style-guide.md`、`reusability-criteria.md`、`evaluation-protocol.md` を全文読む。
3. 次を実行し、出力を保持する。

```bash
bash .claude/skills/lint/lint-check.sh \
  --collection insight:wiki/insight/pages \
  --collection it:wiki/it/pages
```

## 構造チェック

| CHECK | 重大度 | 内容 | 最終判断 |
|---|---|---|---|
| 1 | ERROR | ローカル／クロスコレクションのリンク切れ | スクリプト |
| 1b | WARNING | 禁止されたwikiエイリアス記法 | スクリプト |
| 2 | WARNING | 被参照・発リンクともにない孤立ページ | スクリプト |
| 3 | WARNING | 既存ページタイトルへのリンク漏れ候補 | LLMで誤検知除外 |
| 4 | WARNING | 同一概念の重複・表記ゆれ | LLM |
| 5 | INFO | 複数概念、過大・過小、過剰リンクによる粒度ズレ | LLM。文字数は候補抽出だけ |
| 6 | WARNING | 定義・数値・日付・事実の矛盾 | LLM |
| 7 | INFO | 対比・分類・統合枠組みにできる未接続の合成機会 | LLM |
| 8 | INFO | TINY+ORPHANまたはリダイレクトだけの低価値候補 | LLMで独自内容を確認 |
| 8b | ERROR/WARNING | insight外部ソース節の欠落・要確認・不正ID・不正項目 | スクリプト＋Codex |
| 9 | INFO | insight評価履歴の欠落・旧rubric・記事変更 | スクリプト＋Codex |

itの `LARGE` は分割理由にせず、1技術1ページへの集約を優先する。統合・削除・リダイレクト化は必ずユーザー確認を取る。矛盾、リンク漏れ、低価値候補は修正前に対象記事を読み、誤検知を除く。

### LLM担当チェックの実行手順

スクリプト結果の確認後、indexと全ページをコレクション横断で読み、次を明示的に実行する。

1. **CHECK-4 重複概念**: タイトル・表記ゆれだけでなく、概要、扱う問い、独自情報を比較する。同一技術のitページと個別事例は1技術1ページ方針で統合候補にする。似ていても役割・適用条件が異なるなら除外する。
2. **CHECK-6 矛盾**: 同じ定義、数値、日付、条件、推奨について相反する記述をページ対で示す。外部確認していなければどちらが誤りか断定せず、要確認とする。
3. **CHECK-7 合成機会**: 同じ問いへの異なるアプローチ、複数ページに共通する分類軸、統合枠組みを探す。表面的な類似や単なるリンク追加は合成機会にしない。

各検出には対象ページ、引用または概要上の根拠、判定理由、具体的な対応案を付ける。該当なしも明記する。CHECK-3/5/8候補も対象記事を読んで誤検知を除外する。

スクリプトの主要出力は次のとおり。

- `BROKEN` / `ALIAS` / `ORPHAN` / `MISSING_LINK`
- `METRICS` / `LOW_VALUE` / `OPEN_SUGGESTION`
- `SOURCE_MISSING` / `SOURCE_UNVERIFIED` / `SOURCE_ENTRY_INVALID` / `SOURCE_DUPLICATE_ID`
- `EVALUATION_STATUS rubric_version=N ...`
- `EVALUATION_REQUIRED slug=X reason=missing|rubric|content|metadata|output ...`
- `EVALUATION_HISTORY_WARNING slug=X reason=metadata|output ...`（無効な過去履歴。最新有効評価があれば状態判定を妨げない）
- `REEVALUATE_SCOPE scope=all|required reason=...`
- `SAMPLE_EVALUATION slug=X`（全評価が現行なら品質ドリフト監査用）

## CHECK-8b: 外部ソース

構造チェックは`insight_source_validator.py`の結果を使う。`SOURCE_MISSING`、一次・二次がなく要確認／参考だけの`SOURCE_UNVERIFIED`は評価上Blocking、形式不正や重複IDは保存前ERRORとする。一次・二次があっても核心となる強い主張とsource IDの対応が不明ならCodex評価でMajor、補足的主張だけの対応漏れならMinorとする。URLの文字列から内容や区分を推測せず、frontmatterの旧sourcesへfallbackしない。

## CHECK-9: rubric差分と評価対象の自動決定

評価状態は記事frontmatterの旧 `reviewed` 整数ではなく、`evaluations/insight/<slug>/` にある最新の完全に有効な評価で判定する。有効性にはfrontmatterだけでなく、protocolが定める本文schemaの必須サマリ、6観点、Blocking/Major/Minor等も含む。無効な過去履歴は警告・件数として残すが、有効評価が1件以上あれば最新有効評価の状態判定を妨げない。

- 最新評価なし: その記事を評価する
- metadataは正常だが本文schemaを満たす有効評価がない: `reason=output` で評価する
- 最新 `rubric_version` が現行と異なる記事が1件以上: rubric変更としてinsight全件を再評価する
- rubricは現行だが `target_blob` が現在の記事ハッシュと異なる: 変更記事を再評価する
- 全件が現行かつ内容一致: 構造監査に加え、`SAMPLE_EVALUATION` の3件をCodexで再評価して品質ドリフトだけ確認する

追加オプションを要求せず、対象件数と実行規模を報告してそのまま同じ `/lint` 実行内で進める。Claude Code自身やClaudeのサブエージェントに採点させない。

## Codex一括評価

対象ごとに `evaluation-protocol.md` の通常評価を実行する。

対象とrun manifestは`evaluation_state.py init`で生成し、`next`が返す最大3件だけを本体Bashから並行起動する。結果は`save`でsource診断category、評価本文validator、target hash、metadataを確認する。source構造不正は保存せず、SOURCE_MISSING / SOURCE_UNVERIFIEDは対応するBlocking・score_cap 49・不合格が揃う評価だけ保存する。形式不正や実行失敗は`fail`へ渡す。中断後は`resume`、全体分布と改善キューは`normalize`で毎回再構築する。このhelper自体にCodexを起動させない。

```bash
python3 .claude/skills/lint/evaluation_state.py init --manifest <run-dir>/manifest.json --rubric-version <N> --pages-dir wiki/insight/pages
python3 .claude/skills/lint/evaluation_state.py next --manifest <run-dir>/manifest.json
# 上の最大3件だけを本体Bashからcodex execし、各結果を次で保存する
python3 .claude/skills/lint/evaluation_state.py save --manifest <run-dir>/manifest.json --slug <slug> --body <codex-out.md>
python3 .claude/skills/lint/evaluation_state.py fail --manifest <run-dir>/manifest.json --slug <slug> --error <reason>
python3 .claude/skills/lint/evaluation_state.py resume --manifest <run-dir>/manifest.json
python3 .claude/skills/lint/evaluation_state.py normalize --output <run-dir>/normalized.json
```

- Claude CodeのWriteツールで自己完結プロンプトを `/tmp` に作る
- rubric、再利用性基準、日本語基準、記事全文、出力形式を埋め込む
- 本体Bashから `run_in_background: true` で `codex exec -m gpt-5.6-sol -s read-only` を直接起動する
- `< /dev/null` を必ず付け、結果は `-o` ファイルから読む
- 各記事を独立した新しいCodex実行にし、他記事の点数や前回点数を渡さない
- 結果を `evaluations/insight/<slug>/` に保存する

並行上限は3件とし、3件以下の固定バッチで保存する。run manifest、最大2回のクリーンretry、失敗継続、停止時の扱いは `evaluation-protocol.md` に従う。全プロセスを本体Bashが保持し、サブエージェント経由にしない。

外部検証は `evaluation-protocol.md` の共通方式だけを使う。一括ランキング前は延期できるが、改善対象記事はキュー処理時に実行する。

## ランキングと改善キュー

評価完了後だけでなく毎回、全insight記事の最新有効評価からraw_score、final_score、品質区分、Blocking/Major、最低観点を再集計する。不正metadataの履歴は使わない。前回停止後もこの再構築によりキューを復元する。run manifestは経緯の補助であり、キューの正本ではない。

次の順で安定的に並べる。同順位はfinal_score昇順、slug昇順とする。

1. 採点対象外またはBlockingあり
2. Majorあり
3. final_score 60未満
4. final_score 60〜69
5. final_score 70以上

Blocking/Majorありと70点未満を標準の改善対象とする。最初に全体分布を確認し、その後で一件ずつ `review-page` と同じ内部改善ループを実行する。評価前に全記事を書き換えない。

各記事では、必要な外部検証、Claude Codeによる1〜3項目の改善、新しいCodexによる独立再評価を行う。利用者は途中で停止できる。停止された場合は処理済み件数、未処理件数、次の対象を残す。統合・削除・リダイレクト化、核心の大幅変更は個別確認を取る。

## suggestionと通常の修正

`OPEN_SUGGESTION` は `suggestions/` 直下で、先頭frontmatterに有効な `status: open` と `target:` を持つ提案だけを対象とする。設計書・監査報告などfrontmatterのない文書は含めない。内容と対象ページを読み、適用／却下／スキップを確認する。適用時は `status: applied`、却下時は `status: rejected` にする。

構造上の改善は未処理suggestion → ERROR → WARNING → INFOの順に扱う。明白で局所的な非破壊修正はまとめて提案できる。削除や統合は自動実行しない。

CHECK-4/6/7を含む通常の改善点は、問題、根拠、差分レベルの推奨対応を一件ずつ提示する。本文・リンク修正は承認後に適用する。統合・分割・削除・リダイレクト・新規関係ページは個別確認を取り、スキップ時は変更せず次へ進む。

## 出力形式

```markdown
## Lint結果サマリ

| チェック | ERROR | WARNING | INFO |
|---|---:|---:|---:|
| ... | ... | ... | ... |

### 重複・矛盾・合成機会
- CHECK-4: 対象 / 根拠 / 統合案、または該当なし
- CHECK-6: 対象 / 相反する記述 / 要確認事項、または該当なし
- CHECK-7: 対象群 / 共通構造 / 関係概念案、または該当なし

### 評価状態
- rubric_version: N
- 現行評価: N件
- 未評価: N件
- 旧rubric: N件
- 記事変更後: N件
- 再評価範囲: 全件 / 対象のみ / サンプルのみ

### 品質分布
| 区分 | 件数 |
|---|---:|
| 採点対象外 | N |
| 0〜59 | N |
| 60〜69 | N |
| 70〜79 | N |
| 80〜89 | N |
| 90〜100 | N |

### 改善キュー
| 順位 | slug | final | Blocking | Major | 最低観点 |
|---:|---|---:|---:|---:|---|

### 処理結果
- 改善・再評価済み: N件
- 未処理: N件
- 次の対象: ...
```

1〜4点差は通常の揺れとして扱い、品質区分、Blocking/Major、観点別傾向を報告の中心にする。
