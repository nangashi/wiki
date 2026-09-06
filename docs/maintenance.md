# リポジトリの保守案内

スキル・設定・ツール・運用文書を変更するときに、該当する行から読む。通常の記事作業は対応スキルを入口とし、この文書や接続仕様の全文読込を必要としない。

## 変更対象から探す

以下のパスはリポジトリルート基準。複数にまたがる変更では該当行を組み合わせる。

| 作業 | 最初に読む仕様・手順 | 実装・設定の入口 | 検証 |
|---|---|---|---|
| wikiを追加・登録変更 | [接続仕様：登録と設定](wiki-contract.md#登録と設定) | `wiki/collections.toml`、対象の `wiki.toml`、`tools/wiki/config.py` | 下記の共通テスト、collections、index check。必須ファイルを先に作り、追加だけで共通スキルを変更しない |
| index・リンク処理変更 | [接続仕様：記事・リンク・index](wiki-contract.md#記事リンクindex)、共通CLI | `tools/wiki/wiki_structure.py` | 共通テスト、index check。越境リンク・新規公開拒否・既存公開維持を確認 |
| 共通構造診断変更 | [接続仕様：コマンドの契約](wiki-contract.md#コマンドの契約) | `tools/wiki/lint_check.py`、`tools/wiki/test_wiki_structure.py` | 共通テスト。診断と実行失敗、指定wikiと越境参照の区別を確認 |
| スキル・読込経路変更 | [接続仕様：責務と正本](wiki-contract.md#責務と正本)、下記の読込例 | `.agents/skills/<操作>/SKILL.md`、設定が指すworkflow | skill-creatorのvalidator、相対リンクの存在確認、下記の読込例を追跡 |
| wiki固有の採用・執筆基準変更 | 対象 `wiki.toml` が指すschema・該当workflow・そこから指定された基準 | 対象wiki内の文書。insightの基準変更は次行も確認 | 対象操作から参照先へ到達できるか、他wikiの手順へ影響しないかを確認 |
| insightの評価・公開処理変更 | [評価プロトコル](../wiki/insight/references/evaluation-protocol.md)、[lint手順](../wiki/insight/workflows/lint.md) | `wiki/insight/tools/evaluation_state.py`、`evaluation_validator.py`、`publication.py`、`check.py` | insightテスト。記事／設計rubric version・両本文schema・両hash・設計評価参照・移行対象・既存履歴・再開条件への影響を確認 |
| insightの出典処理変更 | [schema](../wiki/insight/schema.md)、評価プロトコル | `wiki/insight/tools/insight_source_validator.py`、`check.py` | insightテスト。出典形式と主張の支持判断を混同しない |
| 日本語検査変更 | [日本語基準](../wiki/insight/references/japanese-style-guide.md) | `wiki/insight/tools/textlint-check.sh`、`textlint-report.mjs`、`textlint.config.json` | textlintテスト。必須・要判断・参考の区分と実行失敗を確認 |
| 委譲・エージェント設定変更 | [委譲手順](delegation.md)、独立評価に関係する場合は対象wikiのプロトコル | `.codex/config.toml`、`.codex/agents/*.toml` | 役割・モデル・推論強度・権限・履歴分離の整合を確認。設定変更だけで記事評価を起動しない |
| 配置・責務変更 | [接続仕様](wiki-contract.md) | 移動対象とその参照元 | 現行参照を更新し、関係する検証を実行。過去の評価・suggestions内の旧パスは当時の記録として保持 |

## 読み込み経路の確認例

文書を追加・移動するときは、必要になる条件を判断できる入口にリンクを置く。全資料をAGENTS.mdへ列挙しない。共通の実行手順はスキル、wiki固有の判断はworkflow・基準、実装の契約は接続仕様を正本とする。現在の理解・変更判断に必要な理由は該当する正本に併記し、仕様とともに更新する。判断ごとの履歴文書は作らない。

| 依頼 | 必要な読み込み | この段階では不要 |
|---|---|---|
| itの記事から質問に答える | query → 登録・対象設定 → index検索・関連記事 | 執筆基準、insightの評価文書 |
| 回答からinsightへの追記を提案する | query → 対象設定の `workflows.ingest` の採用判断部分 → 指定されたschema・採用基準 | 執筆・独立評価の参照文書。承認後にingestへ引き渡す |
| insightへソースを取り込む | ingest → 設定 → 採用判断 → 採用後に執筆基準 → 評価開始時にプロトコル | 不採用候補に対する執筆・評価文書 |
| insight記事を評価だけする | review-page → 設定・schema・review手順・評価に必要な基準 | 記事・indexの書き換え。既存の評価分離要件は維持 |
| itだけを監査する | lint → it設定・schema・lint手順 → 診断・意味的監査 | insightの評価・改善。越境リンクの存在確認は行う |
| index実装を修正する | この案内の対応行 → 接続仕様・実装・対応テスト | 全記事・全品質基準の全文読込 |

子へは担当範囲に必要な参照先を直接渡し、この案内から探索し直させない。既に読んだ変更のない文書は再読不要。参照先の存在だけでなく、読む条件・担当・終了条件まで到達できるかを確認する。

## 検証コマンド

すべてリポジトリルートから実行する。変更に関係する検証を選ぶ。文書だけの整理で全記事の再評価は起動しない。

```bash
# 共通設定・構造・index・リンク・公開hook
python3 -m unittest discover -s tools/wiki -p 'test_*.py'
# insight固有の評価・出典・公開・旧履歴互換
python3 -m unittest discover -s wiki/insight/tools -p 'test_*.py'
# 日本語検査のfixtures
bash wiki/insight/tools/test-textlint-check.sh
# 読み取り専用の登録・index確認
python3 tools/wiki/wiki_structure.py collections
python3 tools/wiki/wiki_structure.py index --check
```

index checkは不一致時1、実行エラー時2。構造診断は終了コード0でも品質問題を含むため出力を確認する。詳しいCLI契約は [接続仕様](wiki-contract.md#共通cli)。スキルvalidatorの場所・呼び出しは、利用中のskill-creatorスキルを参照する。
