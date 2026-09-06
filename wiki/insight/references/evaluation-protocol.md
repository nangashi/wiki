# insight評価プロトコル

**rubric_version: 6**。 `article-quality-rubric.md`、`reusability-criteria.md`、`japanese-style-guide.md`を全文入力にし、記事ごとにfreshなread-only **evaluator（gpt-5.6-sol / low）** が評価する。執筆会話、前回評価、他記事の結果は渡さない。Astraとeditorは独立評価の判定や根拠を代行しない。集計と公開可否の導出は保存層で行う。

## 記事単独読解と設計照合

記事レビュー担当は設計レビュー・執筆に参加していないfreshなread-only evaluatorとする。

1. helperで評価対象をclaimしてから、記事全文と次の読解質問だけを渡す。「何の概念で何をどう説明するか」「現実の何の見方が変わるか」「比較や行動がある場合、何を見分け、いつ何をするか」「確認されたことと解釈・提案を区別できるか」「どこで理解が止まるか」。設計・資料本文・作者の意図・過去評価は渡さない。回答は「概念と関係」「現実の見方」「確かさ」「理解が止まった箇所」の四つの箇条書き（各一行）で受け、親が一時ファイルへそのまま保存する。
2. 保存後に同じ担当へ記事schema、品質・再利用性・日本語基準、設計、必要な根拠資料を渡す。以下の本文schemaで評価し、第一段階の回答を `## 記事単独読解` に変更せず収録する。誤読の訂正は後段に記す。
3. `## 設計との照合` に到達点D IDごとの本文の実現箇所・不足と `- design_alignment: 合格 / 不合格` を記す。設計に書かれていることを本文の理解に代用しない。不一致は対応する六観点の必須項目へ一度だけ記す。設計自体の不足は設計へ差し戻す。

全記事で設計と設計評価参照を必須とし、不足する場合は通常記事評価のinit・claim・保存を行わない。取り込み・通常レビュー・lintでは先に設計を作成・独立レビューする。評価のみでは不足を報告し作成しない。過去の `未導入` 評価は履歴として読めるが、完成や免除の根拠にしない。初回診断で設計自体が不合格ならその問題も記録し、記事評価のみを工程全体の完成扱いしない。独立設計評価は下記に従う。

## 保存と入力

評価は`evaluations/insight/<slug>/YYYYMMDDTHHMMSSZ-v<rubric_version>-<run-id>.md`へ保存する。時刻はUTCのRFC 3339秒精度、frontmatterは`YYYY-MM-DDTHH:MM:SSZ`、ファイル名は区切りを除いた形式を使う。run-idは開始前に生成する8〜32文字の小文字英数字で、最新はmtimeでなく有効な`evaluated_at`、同時刻ならrun-idで決める。記事frontmatterに評価を保存しない。

```yaml
---
target: "wiki/insight/pages/<slug>.md"
target_blob: "<git hash-objectで得た評価時内容の完全なhash>"
design_target: "wiki/insight/designs/<slug>.md"
design_blob: "<評価対象設計の完全なhash>"
design_evaluation: "<設計評価履歴のパス>"
rubric_version: 6
evaluator: "codex"
evaluator_model: "gpt-5.6-sol"
evaluated_at: "YYYY-MM-DDTHH:MM:SSZ"
run_id: "<8〜32文字の小文字英数字>"
---
```

通常評価は下記の「記事単独読解と設計照合」の二段階で行う。Astraが`git hash-object <対象記事>`（`-w`なし）でtarget_blobを得てから、基準全文、記事全文、以下の本文schema、編集禁止を含む自己完結プロンプトを作る。evaluatorにはfrontmatter、pass、decision、件数を出力させない。標準サブエージェントでfresh/read-only分離を設定できないときだけ、次の独立CLIを使う。run-idごとに異なる絶対`evaluation_prompt`、`evaluation_output`、`evaluation_log`を用意し、親のシェルで実行する。どちらも使えなければ制約を報告し、評価を代行しない。

```bash
codex exec -C . -s read-only -m gpt-5.6-sol \
  -c 'model_reasoning_effort="low"' -c agents.enabled=false --ephemeral \
  -o "$evaluation_output" - < "$evaluation_prompt" > "$evaluation_log" 2>&1
```

`-`は標準入力からプロンプトを読む指定であり、入力を閉じて対話待ちを残さない。親はセッションを保持して完了を回収する。終了コード0や出力ファイルだけではvalidatorとhash確認を省略せず、保存本文は`-o`の出力から読みログと混ぜない。

## evaluator本文schema

```markdown
# Insight記事評価: <slug>
- reusability_gate: 合格 / 不合格

## 再利用性ゲート
- R1: 理由
- R2: 理由
- R3: 理由
- R4: 理由

## 観点別評価
| 観点 | 状態 | 根拠 |
|---|---|---|
| 核心と推論力 | 十分 / 要対応 / 対象外 | ... |
| 論理と構造 | 十分 / 要対応 / 対象外 | ... |
| 有用性と適用境界 | 十分 / 要対応 / 対象外 | ... |
| 事実基盤 | 十分 / 要対応 / 対象外 | ... |
| 情報設計 | 十分 / 要対応 / 対象外 | ... |
| 日本語の自然さ | 十分 / 要対応 / 対象外 | ... |

## 記事単独読解
- 概念と関係: 第一段階の回答。比較がある場合は見分ける軸も含める。
- 現実の見方: 第一段階の回答。行動がある場合はいつ何をするかも含める。
- 確かさ: 第一段階の回答。
- 理解が止まった箇所: 第一段階の回答。なければその旨。

## 設計との照合
- design_alignment: 合格 / 不合格
- D1: 本文の対応箇所と達成状況。設計の全D IDを確認する。

## 対応項目
- なし

## 良い点
- 保持すべき具体的な強み
```

対応項目がある場合は`- なし`の代わりに、優先順で連番の各項目を出す。実際に必要な行動だけを一項目ずつ出し、重複した要約一覧は出さない。

```markdown
### P1: タイトル
- 種別: 修正必須 / 調査必須 / 任意改善
- 観点: 6観点のいずれか / 再利用性
- 対象箇所: 短い原文引用
- 問題: 具体的な問題と読者への影響
- 改善後に満たす条件: 受入条件
- 対応方法: 最小の修正または調査経路
```

`調査必須`にはさらに次を必ず含める。

```markdown
- 確認対象: 検証する具体的な主張
- 必要な理由: 結果が採用・編集判断をどう変えるか
- 調査先: 既存または候補となる一次資料等
- 結果ごとの対応: 支持時=>保持、非支持時=>修正・削除、結論不能時=>不要な主張は省略し、不可欠な主張は採用を保留
```

ゲート合格では6観点を評価する。`要対応`の観点には、その観点の`修正必須`または`調査必須`を一つ以上置く。必須項目の観点は必ず`要対応`にする。ゲート不合格では6観点をすべて`対象外`とし、`再利用性`の`修正必須`を置く。`再利用性`の対応項目はゲート不合格時だけに使う。十分な観点には任意改善を置ける。

## 検証と保存

`evaluation_validator.py`で本文schemaを検証してから保存する。v3/v4/v5 metadataに数値評価の旧本文を受け入れない。v4は機序と介入効果の根拠を区別し、節をまたぐ主要主張の意味的一致を明示的に確認する基準改定であり、本文schemaはv3と共通とする。v5は曖昧な動詞について対象・作用・結果を文脈から特定できるか確認する日本語基準の改定であり、本文schemaは変更しない。validatorはP番号、6観点、状態と対応項目の整合、調査必須の追加フィールド、必須項目の存在を確認する。

source診断のcodeが対応する必須項目に独立した識別子として含まれるかは、evaluation_state.pyの保存処理が検証する。

保存層は本文から次を機械的に導出する。

- `pass`: ゲート合格かつ`修正必須`と`調査必須`が0件。
- `decision`: ゲート不合格なら`対象外`、必須項目があれば`要対応`、それ以外は`公開可`。
- counts: `revision_count`、`research_count`、`optional_count`。

`SOURCE_MISSING` / `SOURCE_UNVERIFIED`は偽であることを意味しない。source validatorの構造診断は保存を拒否する。既存記事の品質診断は、そのcodeを逐語的に含む`事実基盤`の必須項目を持つ非pass評価だけを保存する。概念不採用時は、無意味な全文診断をせず再利用性の必須項目にcodeを置ける。新規公開は現行version、記事・設計の内容一致hash、両評価の導出pass、設計照合合格、source validator成功をすべて要する。

空出力、形式不正、保存時hash不一致、実行失敗は保存しない。本文が変わった場合は旧入力のretryにせず、新しいhashと記事全文で評価し直す。形式・実行エラー時のretryは同一入力で行う。親が信頼できる起動設定・実行情報からmodel、時刻、hashを確定し、evaluatorへ自己申告させない。エラーや前回出力をプロンプトに加えず、同じクリーン入力で新しいevaluatorを最大2回再試行する。すべて失敗したらfailedを記録して次へ進み、評価を代行しない。評価履歴とmanifestの書き込みは親がhelperを通じて直列に行い、評価担当へ委譲しない。

## 改善と外部検証

必須の調査を、依存する本文修正より先に行う。独立した最小修正は並行してよい。調査は対象主張、既存ソース、一次資料優先、確認済み・未確認・誤りの分離を入力にしたfreshなevaluatorへ依頼する。根拠未確認を誤りとして扱わず、結果により保持・修正・削除・保留を決める。

外部検証は通常評価と別run-id・出力ファイルに保存し、次を出力させる。

```markdown
# 外部検証: <slug>
## 確認済み
- 主張 / 根拠 / URL
## 未確認
- 主張 / 確認できなかった範囲 / 推奨対応
## 誤り
- 主張 / 根拠 / 推奨修正 / URL
```

外部検証本文の必須見出しと内容を確認し、不正なら同じ入力で新しい履歴なしのevaluatorへ最大2回再試行する。外部検証履歴は`evaluations/insight/<slug>/external/<evaluation-run-id>-external-<run-id>.md`に保存する。

保存時のfrontmatterには`target`、`target_blob`、`evaluation_run_id`、`evaluator`、`evaluator_model`、`verified_at`、`run_id`を付ける。調査不能は未確認であり誤りではない。

実質的修正では先に[設計手順](../workflows/design.md)を実行する。設計の問題を本文の追加だけで処理しない。Astraが必須対応から1回につき1〜3項目を選び、必要な調査後にeditorへ最小修正を委譲する。[委譲手順の小作業の直接処理](../../../docs/delegation.md#小作業の直接処理)に該当する修正はAstraが担当する。修正担当は改稿後に[執筆手順の草稿・改稿後の確認](../workflows/ingest.md#草稿改稿後の確認)を行う。本文・外部ソース・関連リンクを先に確定し、変更したinsight記事はすべて最終評価する。最終評価後は記事・設計blobを変更せず、評価履歴・公開判断・残課題を共通スキルへ返す。index生成は共通スキルが担当する。

ゲート合格かつ必須項目がなければ任意改善を残して終了する。設計と本文を往復する一連の改善で最大3巡、または同じ実質的な必須項目が2回続けば停止し、未解決事項を報告する。外部検証と記事変更の後は、前回評価を渡さないfreshな独立評価で最終記事を確認する。

## 履歴・一括処理

旧v1/v2/v3/v4/v5は履歴として読めても現行評価にはしない。validatorは明示された`--rubric-version`を優先し、なければmetadata version、raw bodyでは6を使う。新規init/saveは旧versionを拒否する。旧rubricの有効評価が1件でもあれば、`$lint`実行時に全件再評価する。評価欠落やmetadata不正だけの場合は該当記事を再評価する。旧runの未完了状態をv6としてresumeしない。

`evaluation_state.py`はmanifest、retry/failed/pending、resume、保存、正規化だけを担当し、evaluatorを起動しない。run開始時は`evaluations/insight/runs/YYYYMMDDTHHMMSSZ-<run-id>/manifest.json`を状態の正本、`manifest.md`を表示として作る。最大3件の固定バッチで評価し、各結果を保存・検証してからmanifestへ追記する。中断時は新しいバッチを始めず、進行中の保存可能な結果とmanifestを確定する。`normalize`の分布キーは`対象外`、`修正・調査必須`、`修正必須`、`調査必須`、`公開可`、`再評価必要`を排他的に使う。現行version・内容一致の必須または不合格だけをキューに置き、順序は`対象外`、修正あり、調査のみ、slugとする。件数は品質順位ではない。旧版・欠落・内容不一致は再評価必要として別に報告する。


通常評価の保存も共通helperを使う。`init`と`next`で対象と評価開始時のhashを記録してから評価を起動する。`save`は開始時と保存時のhash一致を確認する。手動で本文の合否や対応項目を補完しない。

```bash
python3 wiki/insight/tools/evaluation_validator.py <evaluator-out.md> --slug <slug> --rubric-version 6
python3 wiki/insight/tools/evaluation_state.py init --manifest <run-dir>/manifest.json --rubric-version 6 --target <slug>:wiki/insight/pages/<slug>.md --design-evaluation <design-history.md>
python3 wiki/insight/tools/evaluation_state.py next --manifest <run-dir>/manifest.json
python3 wiki/insight/tools/evaluation_state.py save --manifest <run-dir>/manifest.json --slug <slug> --body <evaluator-out.md> --design-evaluation <design-history.md>
```

一括評価では、上記の `init --target` の代わりに対象全体を指定できる。全対象の記事に対応する設計評価を `--design-evaluation` でそれぞれ指定する。失敗・中断後の再開・分布の再構築も同じhelperを使う。

```bash
python3 wiki/insight/tools/evaluation_state.py init --manifest <run-dir>/manifest.json --rubric-version 6 --pages-dir wiki/insight/pages --design-evaluation <design-history-1.md> --design-evaluation <design-history-2.md>
python3 wiki/insight/tools/evaluation_state.py fail --manifest <run-dir>/manifest.json --slug <slug> --error <reason>
python3 wiki/insight/tools/evaluation_state.py resume --manifest <run-dir>/manifest.json
python3 wiki/insight/tools/evaluation_state.py normalize --output <run-dir>/normalized.json
```


## 設計レビュー

設計基準versionは `design-quality-rubric.md` の **design_rubric_version: 1**。記事versionと独立に管理する。Astraが設計を作成して固定し、freshなread-only evaluator（Sol / low）へ設計全文、設計schema、設計・再利用性基準、必要資料を渡す。執筆会話・旧評価を渡さない。評価者は記事を執筆しない。

設計評価本文は次の形式を使う。必須項目、ゲート、観点状態の整合、修正必須／調査必須／任意改善の定義、retryは記事評価と同じ。観点だけ以下の五つにする。ゲート不合格時は五観点を対象外にし、再利用性の必須項目を置く。

```markdown
# Insight設計評価: <slug>
- reusability_gate: 合格 / 不合格

## 再利用性ゲート
- R1: 理由
- R2: 理由
- R3: 理由
- R4: 理由

## 観点別評価
| 観点 | 状態 | 根拠 |
|---|---|---|
| 読者・目的 | 十分 / 要対応 / 対象外 | ... |
| 読後の到達点 | 十分 / 要対応 / 対象外 | ... |
| 内容と順序 | 十分 / 要対応 / 対象外 | ... |
| 主張と根拠・境界 | 十分 / 要対応 / 対象外 | ... |
| 採用・省略 | 十分 / 要対応 / 対象外 | ... |

## 対応項目
- なし

## 良い点
- 保持すべき具体的な強み
```

設計の履歴は `evaluations/insight/<slug>/design/YYYYMMDDTHHMMSSZ-v1-<run-id>.md`。metadataは記事と同じ七フィールドを使い、targetは `wiki/insight/designs/<slug>.md`、target_blobは設計hash、rubric_versionは設計versionとする。評価者へ自己申告させず親がhelperで保存する。内容が変われば設計を再評価し、同じ本文でも記事の読解・照合を再評価する。

## 設計と記事の完成条件

設計必須化は評価開始・完成条件の変更であり、記事・設計の品質判定基準は変えないため、rubric versionは据え置く。既存の設計・記事の組は引き続き内容と評価参照で検証し、設計参照のない旧評価は完成扱いしない。

記事v6のmetadataは従来の七フィールドに `design_target`、`design_blob`、`design_evaluation` を加え、照合対象と設計評価を追跡する。不合格設計を参照する記事診断も保存できるが、工程完了には設計の合格を要する。設計参照を持たない旧runは新しい通常評価として再開・保存できない。設計・記事のhash、基準version、設計評価参照が現在と一致し、両方の必須項目が0、記事の照合が合格、機械検査が成功した組だけを工程完了とする。設計自身に承認欄は設けない。

設計blobが変わった場合、設計評価が不合格へ変わった場合、または設計基準versionが変わった場合は古い組の合格を使わない。claim・保存・再開時も両入力とversionを確認する。設計評価の保存失敗や未実施は記事評価で代替しない。

全記事で設計を必須とし、導入記録・移行免除一覧は持たない。設計がなければ通常の書込み操作で作成・独立レビュー・記事との照合を行う。読み取り専用チェックと明示的な評価のみでは不足を報告し、完成扱いしない。既存index掲載は評価失効だけでは削除しないが、更新完了にはworkflowとcheckでも組の整合を確認する。indexは旧公開本文のスナップショットではない。


## 設計と記事のhelper呼び出し

```bash
# 設計はclaim後に独立レビューする。実行状態はrun manifestに保存する。
python3 wiki/insight/tools/evaluation_state.py init --kind design --rubric-version 1 --manifest <design-run>/manifest.json --target <slug>:wiki/insight/designs/<slug>.md
python3 wiki/insight/tools/evaluation_state.py next --manifest <design-run>/manifest.json
python3 wiki/insight/tools/evaluation_state.py save --manifest <design-run>/manifest.json --slug <slug> --body <design-evaluator-out.md>

# 記事は設計レビュー参照をinit時に固定し、saveにも同じ参照を渡す。
python3 wiki/insight/tools/evaluation_state.py init --rubric-version 6 --manifest <article-run>/manifest.json --target <slug>:wiki/insight/pages/<slug>.md --design-evaluation <design-history.md>
python3 wiki/insight/tools/evaluation_state.py next --manifest <article-run>/manifest.json
python3 wiki/insight/tools/evaluation_state.py save --manifest <article-run>/manifest.json --slug <slug> --body <article-evaluator-out.md> --design-evaluation <design-history.md>
```

複数記事では `--target` と `--design-evaluation` を記事ごとに繰り返せる。設計参照のslugは履歴のパスとmetadataから検証する。最大3件のbatchの全入力を検査してからclaimする。設計変更後にresumeすると旧入力の保存を認めず、変更理由を残す。新しい設計を評価後、新しい参照を持つrunをinitする。親は旧runの未処理と新runへの引き継ぎ先を報告する。

記事単独読解の先保存と、後段評価へ収録した原文の一致は親が確認する。helperによる本文schema検査だけで二段階実行済みとみなさない。機械検査は設計の五見出しとD IDの一意性、記事照合の全D ID対応も検証するが、到達点の妥当性は独立担当が評価する。
