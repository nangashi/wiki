# insight記事の評価・改善プロトコル

このファイルは `$ingest`・`$review-page`・`$lint` が共有する内部手順であり、利用者が直接起動するスキルではない。

## 役割の境界

- Astra: ワークフロー統括、検証済みメタデータの付与、採用・改善方針・終了判定
- `editor`（Terra）: 指定記事の作成・改善。Astraが必要な原文と差分を確認する
- `evaluator`（Sol / low）: 独立評価と必要時の外部検証。記事・index・評価履歴を変更しない
- 再評価は新しい履歴なしのevaluatorを起動し、執筆会話、前回評価、他記事の点数を渡さない

Astraとeditorはルーブリックを執筆・改善の基準として参照してよいが、自分で採点しない。評価モデルは既存履歴との比較のため `gpt-5.6-sol` に固定する。モデルを変える場合は別途評価の比較方法を決め、実際と異なるモデル名を記録しない。

## 評価履歴と識別子

通常評価は次へ保存する。

```text
evaluations/insight/<slug>/YYYYMMDDTHHMMSSZ-v<rubric_version>-<run-id>.md
```

- 時刻はUTCのRFC 3339秒精度を使う。frontmatterは `YYYY-MM-DDTHH:MM:SSZ`、ファイル名は区切りを除いた `YYYYMMDDTHHMMSSZ` とする
- `run-id` はAstraが評価開始前に生成する小文字英数字8〜32文字の一意識別子とする。同一秒の衝突を防ぐ
- 最新評価はmtimeでなく、有効なfrontmatterの `evaluated_at`、同時刻なら `run_id` の辞書順で決める
- ディレクトリは最初の結果保存時に作る。記事frontmatterへ点数を保存しない

評価ファイル冒頭のfrontmatterはAstraが付与する。evaluatorへtarget、blob、version、時刻、モデルを自己申告させない。モデルは起動設定・実行情報から確認する。

```yaml
---
target: "wiki/insight/pages/<slug>.md"
target_blob: "<git hash-objectで得た評価時内容の完全なhash>"
rubric_version: 2
evaluator: "codex"
evaluator_model: "gpt-5.6-sol"
evaluated_at: "YYYY-MM-DDTHH:MM:SSZ"
run_id: "<8〜32文字の小文字英数字>"
---
```

## 通常評価

1. `article-quality-rubric.md`、`reusability-criteria.md`、`japanese-style-guide.md` と対象記事を全文読む。
2. Astraが `git hash-object <対象記事>` で `target_blob` を得る。`-w` は使わない。rubric version、UTC時刻、run-id、出力先もこの時点で確定する。
3. 必要な場合だけ関連ページのタイトルとindexサマリを加える。リンク数・孤立・周辺ページ品質を本文100点へ混ぜない。
4. Astraが基準全文、記事全文、本文出力schema、ファイルを編集しない制約を含むクリーンな自己完結プロンプトを用意する。同じ入力で再試行できるよう `/tmp/codex-evaluate-insight-<slug>-<run-id>-prompt.md` へ保存してよい。メタデータfrontmatterは出力させない。
5. Codex標準のサブエージェント機能で新しい `evaluator`（`gpt-5.6-sol` / low、read-only）を起動する。会話履歴を引き継がない起動（対応ツールでは `fork_turns="none"`）を選び、手順4の入力だけを渡す。評価のたびに新しいスレッドを使い、執筆担当や前回評価スレッドを再利用しない。標準機能で履歴分離やread-onlyを設定できない場合だけ、下記の独立CLI実行を使う。どちらも利用できなければ制約を報告し、Astraやeditorで採点を代行しない。
6. 完了したevaluatorの本文をAstraが変更せず `/tmp/codex-evaluate-insight-<slug>-<run-id>-out.md` に保存し、共通validatorで検証する。ツールのJSONラッパーやコードフェンスを評価本文へ混ぜない。必須見出し、R1〜R4、6観点の0〜5・換算点・配点・根拠、raw_scoreの合計、score_capとfinal_score、品質区分、合否、Blocking/Major/Minor、改善項目schemaをすべて構造・算術検証する。
7. 空出力、形式不正、算術不整合、実行失敗ならその出力を破棄する。前回出力、前回点数、検証エラーをプロンプトへ加えず、同じクリーンな自己完結プロンプトを使って新しい履歴なしのevaluatorを起動する。Astraが点数を訂正・補完しない。
8. 正常な本文に、手順2で確定したfrontmatterをAstraが付与して評価履歴へ保存する。保存直前に記事へ`insight_source_validator.py`を実行する。`category=structure`の診断は保存を拒否する。既存記事の`category=quality`は、対応する`SOURCE_MISSING` / `SOURCE_UNVERIFIED` codeを逐語的に含むBlocking、score_cap 49、`pass: いいえ`が評価本文に揃う場合だけ保存し、改善queueへ載せられる。記事hashが変わっていないことも確認する。

評価履歴とmanifestへの書き込みはAstraが既存helperを使って直列に行う。評価担当に保存やmetadata付与を委譲しない。

共通validatorは次であり、`$ingest`・`$review-page`・`$lint`の保存前とclean retry判定で必ず同じものを使う。失敗した本文を手修正したりCURRENTとして扱ったりしない。

```bash
python3 .agents/skills/lint/evaluation_validator.py <codex-out.md> --slug <slug>
```

### クライアント互換用の独立CLI実行

標準サブエージェントで必要な分離を設定できない場合に限る。Astraが手順4の自己完結プロンプトにevaluatorの担当指示も含め、run-idごとに異なる `evaluation_prompt`、`evaluation_output`、`evaluation_log` の絶対パスを用意する。リポジトリルートで親のシェルツールから直接実行する。

```bash
codex exec -C . -s read-only -m gpt-5.6-sol \
  -c 'model_reasoning_effort="low"' -c agents.enabled=false --ephemeral \
  -o "$evaluation_output" - < "$evaluation_prompt" > "$evaluation_log" 2>&1
```

`-` はプロンプトを標準入力から読む指定であり、ファイル終端で入力を閉じる。対話待ちのstdinを残さない。親はシェルツールのセッションIDで実行を保持し、完了まで結果を回収する。終了コード0かつ出力ファイルが存在しても、手順6以降のvalidator・hash確認を省略しない。失敗・空出力は同じ入力で最大2回だけ新規実行し、resume/forkや前回点数は使わない。記事評価履歴に保存する本文は `-o` のファイルから読み、ログとは混ぜない。

### Codex本文の出力schema

```markdown
# Insight記事評価: <slug>

- reusability_gate: 合格 / 不合格
- raw_score: N / 採点対象外
- score_cap: なし / 49 / 59 / 採点対象外
- final_score: N / 採点対象外
- verdict: 公開品質 / 良好。軽微な改善のみ / 利用可能だが改善対象 / 主要な修正が必要 / 構造的な書き直しが必要 / 採点対象外
- pass: はい / いいえ

## 再利用性ゲート
- R1: ...
- R2: ...
- R3: 該当なし / ...
- R4: ...

## 点数内訳
| 観点 | 0〜5 | 点数 | 配点 | 根拠 |
|---|---:|---:|---:|---|
| 核心と推論力 | ... | ... | 25 | ... |
| 論理と構造 | ... | ... | 20 | ... |
| 有用性と適用境界 | ... | ... | 15 | ... |
| 事実基盤 | ... | ... | 15 | ... |
| 情報設計 | ... | ... | 10 | ... |
| 日本語の自然さ | ... | ... | 15 | ... |

## Blocking
- なし / 問題、適用上限、根拠

## Major
- なし / 問題と根拠

## Minor
- なし / 問題と根拠

## 改善項目
### P1: <短い名称>
- 対象箇所: 「短い引用」
- 問題: ...
- 改善後に満たす条件: ...
- 改善方法: ...
- 要外部調査: はい / いいえ

## 良い点
- 改善時に保持すべき具体的な長所
```

該当問題がなくても各見出しを残す。採点対象外でもゲート根拠、Blocking、改善項目、良い点を出す。

ゲート合格時は6観点を0〜5の整数で採点する。ゲート不合格時は6行を残し、0〜5と点数の欄をすべて`採点対象外`にする。問題がなく改善項目が不要な場合は`## 改善項目`直下を`- なし`とする。それ以外はP1から連番にし、5つの必須フィールドをすべて書く。

## 外部検証

次のいずれかなら外部検証する。

- `## 外部ソース`が参考・要確認のみ、一次・二次ソースの適格性が不明、またはアクセス不能
- 数値、実験結果、研究名、メタ分析、固有介入の効果を主要根拠にする
- 核心を支える強い経験的主張の追跡先が不明
- 時間で変わりうる事実を含む
- 通常評価に `要外部調査: はい` がある

外部検証も通常評価と同じく、新しい履歴なしのevaluator（Sol / low、read-only）に自己完結プロンプトを渡す。通常評価とは別のrun-idと出力ファイルを使い、記事全体の点数や過去の評価本文は渡さない。対象主張、記事末尾の既存外部ソース、一次資料優先、確認済み／未確認／誤りの分離、URL、次の本文schemaを要求する。

```markdown
# 外部検証: <slug>
## 確認済み
- 主張 / 根拠 / URL
## 未確認
- 主張 / 確認できなかった範囲 / 推奨対応
## 誤り
- 主張 / 根拠 / 推奨修正 / URL
```

通常評価と同様に本文schemaを検証し、不正出力は破棄してクリーンな同一プロンプトで新しい履歴なしのevaluatorを起動する。Astraが次のfrontmatterを付け、元評価へ紐づけて保存する。

```text
evaluations/insight/<slug>/external/<evaluation-run-id>-external-<run-id>.md
```

frontmatterには `target`、`target_blob`、`evaluation_run_id`、`evaluator: "codex"`、`evaluator_model: "gpt-5.6-sol"`、`verified_at`、`run_id` を持たせる。調査不能は「未確認」であり「誤り」ではない。

`$ingest` と `$review-page` は改善前に必要な外部検証を行う。`$lint` 一括評価だけは全件ランキングを先に完成させ、改善対象になった記事の検証をキュー処理時まで延期できる。この延期は外部検証の実行方式や基準を変えない。

## 改善ループ

1. Blocking、Major、最低点の観点を優先する。
2. Astraが改善項目を選び、editorへ1回につき1〜3項目だけ改善を委譲する。小さな修正や核心の難しい判断はAstraが担当してよい。良い点を保持し、点数目的で説明を足し続けない。
3. 外部検証が必要な主張は検証後に直す。未確認なら削除・留保・出典要求から選ぶ。
4. 本文・外部ソース・関連リンクを先に確定する。相互リンクのためだけに関連先を更新しない。関連先にも意味上必要な修正があれば、変更した全insightページを評価対象へ加える。
5. 前回点数・評価本文を渡さない新しい通常評価を、変更された全insightページへ行う。
6. 1〜4点差だけで修正を繰り返さず、品質区分、Blocking/Major、観点別傾向を比較する。

最終評価の保存後に記事blobを変更しない。変更が必要ならその評価を最新扱いせず再評価する。indexは全変更ページの最終評価後に`wiki_structure.py index`で生成する。index生成や被リンク取得だけでは記事blobを変更せず、再評価も発生しない。

合格条件はraw_score 80以上、6観点すべて3/5以上、Blocking/Major 0件。最大3回、または2回続けて品質区分が変わらず同じMajorが残れば停止し、残課題を報告する。

## `$lint` の一括評価と再開

`lint-check.sh` は有効な評価frontmatterと、キュー再構築に必要なCodex本文schemaの両方を検証し、完全に有効な履歴だけから最新評価を `evaluated_at` と `run_id` で決める。不正な過去履歴は警告するが、より新しい有効評価を無効化しない。有効評価が0件の場合、metadata不正は `reason=metadata`、本文不正は `reason=output` とする。未評価・旧rubric・記事変更後もそれぞれ再評価対象とし、有効な旧rubric評価が1件でもあればinsight全件を現行rubricで評価する。

一括処理は固定上限3件で並行し、3件以下のバッチ単位で行う。状態管理には`.agents/skills/lint/evaluation_state.py`を使う。このhelperはCodexを起動せず、対象・manifest、次バッチ、validator、metadata付与と保存、retry/failed/pending、resume、最新評価の正規化、品質分布、安定sortの改善queueだけを担当する。evaluatorの起動・結果回収はAstraがCodex標準のサブエージェント機能で行う。manifestの更新・結果保存は並列化しない。

1. run開始時に `evaluations/insight/runs/YYYYMMDDTHHMMSSZ-<run-id>/manifest.json` を状態更新の正本として作り、同じ場所の`manifest.md`を人間向け表示として自動生成する。rubric version、対象、開始時刻、状態を記録する。
2. 各バッチの結果を個別評価履歴へ保存して検証してから、manifestへ成功・失敗・retry回数を追記する。
3. 失敗はクリーンな同一プロンプトで最大2回再試行する。初回と最大2回の再試行がすべて失敗したらfailedとして次の記事へ進み、Astraが採点しない。
4. 停止指示や中断を検知したら新規バッチを開始せず、進行中バッチの保存可能な結果とmanifestを確定して停止する。

改善キューはmanifestの一時リストを正本にしない。各 `$lint` 実行で、全記事の最新有効評価から採点対象外、Blocking、Major、final_score 70未満を再集計して復元する。前回manifestは処理経緯・失敗理由・次候補の補助情報として使えるが、記事や評価が変われば再構築結果を優先する。

並び順は採点対象外／Blockingあり、Majorあり、60未満、60〜69、70以上。同順位はfinal_score昇順、slug昇順。Blocking/Majorありと70未満を標準改善対象とし、同じ対話内で `$review-page` 相当の改善・再評価を一件ずつ行う。
