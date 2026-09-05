# Wikiと共通スキルの接続仕様

このファイルは現在有効な設定・呼び出し・責務の契約を定義する。判断理由は [ADR 0001](adr/0001-independent-wiki-policies.md)。通常の記事作業では対象wikiの設定と操作手順を読み、この文書全文やADRを毎回読む必要はない。

## 責務と正本

| 所有者 | 正本と責務 |
|---|---|
| リポジトリ | `AGENTS.md`は入口と共通方針、`.codex/agents/`はモデル・役割・権限 |
| 登録一覧 | `wiki/collections.toml`はwiki IDと設定の所在のみ |
| 共通スキル | `.agents/skills/`は対象選択・読込・進行・報告。wiki固有の基準・名前による分岐を持たない |
| 共通ツール | `tools/wiki/`は設定読込・記事探索・リンク解決・index生成・構造診断 |
| 各wiki | `wiki.toml`は目的と参照先、schemaは形式・粒度・出典、workflowsは操作手順、referencesは品質・採用基準、toolsは固有処理 |

wikiの運用文書はスキルの支持文書であり、wiki側へ別のSKILL.mdを作らない。同じ評価ループ・基準を複数入口へ複製しない。各操作手順からwiki内の正本を参照する。共通化は現在共有しているMarkdown・index・リンク形式までとし、評価尺度や履歴schemaまで汎用化しない。

## 登録と設定

`wiki/collections.toml`:

```toml
[collections]
example = "example/wiki.toml"
```

登録先のパスは登録一覧のあるディレクトリからの相対パス。IDは英小文字・数字で始まり、以後は英小文字・数字・ハイフン。設定の`id`と登録IDを一致させる。

各wikiの最小設定:

```toml
id = "example"
purpose = "どんな知識を、どんな判断・理解のために保存するか"
pages = "pages"
index = "index.md"
schema = "schema.md"

[workflows]
ingest = "workflows/ingest.md"
review = "workflows/review.md"
lint = "workflows/lint.md"

[checks]
commands = []

[publication]
mode = "direct"
```

`pages`、`index`、`schema`、各workflowのパスはその設定ファイルのディレクトリ基準。記事ディレクトリ・index・schema・3つのworkflowは用意してから登録する。`purpose`は選択に十分な短い説明にし、詳細な採用基準はworkflowが参照する文書へ置く。専用query手順は現時点では不要。

`publication.mode`は必ず明示する。`direct`は機械的な公開審査なしであり、執筆・品質確認を省略する意味ではない。`checked`では次のcommandを必須とする。

```toml
[publication]
mode = "checked"
command = ["python3", "wiki/example/tools/publication.py"]
```

Python 3.11以降では標準`tomllib`、Python 3.8〜3.10では同梱のTomliを使う。TOMLの独自パーサーは維持しない。同梱コードのライセンス・取得元・ハッシュは `tools/wiki/_vendor/` に保存する。

## コマンドの契約

設定のコマンドは文字列の引数配列とし、shellを介さずリポジトリルートをcwdとして実行する。引数内のファイルパスはルート基準。展開を前提とする`~`、環境変数、globを書かない。固定引数の後ろへ共通ツールが以下を追加する。

| 用途 | 追加引数 | 結果 |
|---|---|---|
| `checks.commands`の各コマンド | `--root <絶対repo-root>` | 0: 診断完了。品質問題は診断に出してよい。非0: 実行失敗 |
| `publication.command` | `--root <絶対repo-root> --slug <slug>` | 0: 新規公開可、1: 条件未達、その他: 実行失敗 |

検査・公開判定コマンドは読み取り専用とし、記事・index・評価履歴を更新しない。評価の起動・改善・履歴保存はworkflowを実行する親が調整する。実行不能・設定不正・必要入力の欠落を「問題なし」「公開可」に変換しない。

共通スキルへ引き渡す状態は、変更対象、実施した検査・評価と根拠の場所、公開／保留、残課題・停止理由を含める。wiki固有の詳細な評価出力はそのwikiのschemaに従い、異なる尺度を合算しない。

## 共通CLI

ルートから実行する。ルート外から呼ぶ場合はスクリプトを絶対パスで指定し、`--root <repo-root>`を付ける。

```bash
python3 tools/wiki/wiki_structure.py collections
python3 tools/wiki/wiki_structure.py index --collection <id> --check
python3 tools/wiki/wiki_structure.py index --collection <id>
python3 tools/wiki/wiki_structure.py index --collection <id> --add <id>:<slug>
python3 tools/wiki/wiki_structure.py backlinks <id>:<slug>
python3 tools/wiki/lint_check.py --collection <id> --checks
```

`index`と構造検査でcollectionを省略すると全登録wikiを選ぶ。構造検査の`--collection`は複数指定できる。`--checks`は選択したwikiの固有検査だけを追加実行する。機械検査コマンドを直接実行してもLLMによる意味的監査・再評価・改善は起動しない。`$lint`は診断を使い、各workflowに定義された処理まで同じ実行内で進める。

indexの`--check`は不一致時1、実行エラー時2、それ以外0。構造検査は診断完了時0であり、stdoutの`BROKEN`等も確認する。固有検査の非0は完了扱いにしない。

## 記事・リンク・index

共通ツールの対象記事は設定のpages直下の`<slug>.md`。slugはIDと同じ文字規則。現行の全wiki横断slug一意規則を維持する。重複は採用時・監査時に確認する。共通構造検査は`CHECK-0`の`DUPLICATE_SLUG`で報告し、新規index追加は他wikiとslugが重複すれば書き込み前に拒否する。

- `[[slug]]`は同一wiki、`[[wiki-id:slug]]`は登録wikiの参照。
- エイリアス記法`[[slug|表示名]]`は禁止。本文では日本語の概念名を先に書き、括弧内にwikiリンクを置く。
- リンクの意味的な関係は記事で説明し、相互リンクだけを目的に関連先を更新しない。
- 単独wikiのリンク検査でも参照先の存在・被リンクは登録全体から解決する。診断対象・固有検査・意味的監査は指定wikiに限定する。
- 記事概要は`## 概要`の最初の段落。indexサマリはこれを改行だけ折り畳んで生成する。indexのカテゴリと既存公開項目を保持する。
- 新規記事は`--add`で明示し、checkedの場合だけ公開判定を呼ぶ。既存公開記事の評価が古くなっても、それだけでindexから落とさない。消えた記事へのindex項目は生成時に除く。
- 全対象indexの生成内容と新規公開条件を確認してから書き込みを始める。公開判定失敗時はどのindexも書き換えない。ファイルシステム障害まで含めた複数ファイルのトランザクションは提供しない。

## 読み込みと委譲

通常はAGENTS.mdと選択したスキル → 設定 → 対象操作手順 → 必要な基準・記事の順に読む。対象明示時は他wikiの品質文書を読まない。queryは記事・indexを検索し、運用文書と評価履歴を回答の知識ソースへ混ぜない。

子には対象記事・必要な基準・許可された編集範囲・出力schema・完了条件を渡す。独立評価はwikiのプロトコルに従い、前回評価や執筆会話を渡さない。履歴・indexの更新は親が直列化する。モデル設定をwiki側へ複製しない。

## 変更時の検証

```bash
python3 -m unittest discover -s tools/wiki -p 'test_*.py'
python3 -m unittest discover -s wiki/insight/tools -p 'test_*.py'
bash wiki/insight/tools/test-textlint-check.sh
python3 tools/wiki/wiki_structure.py index --check
```

共通実装は仮の第三wiki、選択範囲の分離、越境リンク、checkedの許可・拒否・失敗、既存公開維持を検証する。固有実装はそのwikiのテストで検証する。設定・ツールの移行では記事・index・評価履歴のパスと内容を保ち、既存評価状態の一致を確認する。新しいwikiの追加だけで共通スキル本文を変更しないことを受入条件とする。
