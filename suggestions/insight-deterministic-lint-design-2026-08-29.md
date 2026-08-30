# insight独自lint構想（2026-08-29）

## 結論

insight独自lintは新しい汎用校正ツールとして作らず、`wiki/insight/schema.md` にある保存条件を決定論的に検証する薄いvalidator群として、既存の `.claude/skills/lint/` に統合する。

実行経路は次の2つに分ける。

1. **保存時lint**: Claude Codeの`PostToolUse`から、変更されたinsight記事だけを1秒以内で検査する。保存条件に違反するERRORは直ちにClaudeへ返す。
2. **全体lint**: 既存の`/lint`から、全ページ、index、コレクション間リンクを検査する。孤立ページやリンク漏れ候補など、全体走査や判断を要する項目はこちらに残す。

独自lintが担当するのは「形式に適合するか」「参照先が存在するか」の判定までとする。核心、推論力、論理、主張の正しさ、ソースの適格性、日本語の自然さは決定論的に判定できないため、Codex評価または別の校正ツールへ残す。

## 目的

- schema違反を記事作成直後に検出し、後続の評価や全体lintへ不正な記事を渡さない
- 同じ規則を`/ingest`、`/review-page`、`/lint`、Hookで共有する
- LLMによる目視確認を、機械的に判定できない問題へ集中させる
- 診断codeを安定させ、テスト、Hook、CI、評価処理から同じ結果を利用できるようにする

## 対象範囲

### 独自lintが判定するもの

- ファイル名、frontmatter、見出し、必須セクションの形式
- wikiリンクの構文とリンク先の存在
- 外部ソース節と本文中source IDの参照整合性
- indexとpagesの機械的な整合性
- schemaで明示的に禁止された旧形式や一時状態

### 独自lintが判定しないもの

- 記事が概念の本質を捉えているか
- 1ページの概念粒度が適切か
- 概要と詳細の論理が接続しているか
- 経験的主張にsource IDを付けるべきか
- URL先が実際に主張を支えているか
- 一次・二次・参考の分類が正しいか
- 「本質」「核心」「構造」などの語が文脈上冗長か
- 記事がAIらしいか、人間らしいか
- 外部URLが現在到達可能か

後者をERRORにすると、決定論的lintではなく不安定な品質評価になる。候補抽出が必要ならWARNINGまたはINFOとして別レーンへ出し、保存を妨げない。

## 現状

既存の `.claude/skills/lint/lint-check.sh` は、すでに次を検査している。

- 同一コレクションおよびクロスコレクションのリンク切れ
- 禁止されたwikiエイリアス記法
- 孤立ページ
- リンク漏れ候補
- 粒度・低価値ページ候補のためのメトリクス
- insight外部ソース構造
- 記事品質評価の更新要否

また、`insight_source_validator.py` は次を実装済みである。

- frontmatterの旧`source`・`sources`禁止
- `## 外部ソース`の個数と末尾配置
- source項目形式
- S IDの重複、連番、本文からの不正参照
- 一次・二次ソース不在
- `topic:`および一時的な未確認形式の検出

不足しているのは、記事単体の保存条件をまとめて検証する入口と、frontmatter・見出し・indexの追加検査である。既存ロジックを複製せず、Python validatorへ集約して`lint-check.sh`から呼び出す。

## 検査仕様

### A. ファイルとfrontmatter

| code | 重大度 | 条件 |
|---|---|---|
| `FILE_SLUG_INVALID` | ERROR | ファイル名が英数字のkebab-caseでない |
| `FRONTMATTER_MISSING` | ERROR | 文頭にYAML frontmatterがない |
| `FRONTMATTER_INVALID` | ERROR | YAMLとして解析できない、またはmappingでない |
| `FRONTMATTER_KEY_MISSING` | ERROR | `title`、`created`、`updated`のいずれかがない |
| `FRONTMATTER_KEY_FORBIDDEN` | ERROR | `source`、`sources`、新規ページの`reviewed`など禁止keyがある |
| `FRONTMATTER_KEY_UNKNOWN` | ERROR | schemaにないkeyがある |
| `FRONTMATTER_DATE_INVALID` | ERROR | 日付が`YYYY-MM-DD`でない、または実在しない日付 |
| `FRONTMATTER_DATE_ORDER` | ERROR | `updated`が`created`より前 |
| `FRONTMATTER_TITLE_INVALID` | ERROR | `title`が空、文字列でない、前後に空白がある |

既存ページの`reviewed`は移行履歴として許容されているため、単純な全面禁止にはしない。Git差分を参照して新規ページだけ禁止するか、当面はWARNINGとして段階的に扱う。

YAMLを正規表現だけで解釈しない。frontmatter keyの順番や引用符の有無は、schemaが要求していない限りlint対象にしない。

### B. 文書構造

| code | 重大度 | 条件 |
|---|---|---|
| `H1_MISSING` | ERROR | H1がない |
| `H1_MULTIPLE` | ERROR | H1が複数ある |
| `TITLE_H1_MISMATCH` | ERROR | frontmatterの`title`とH1が一致しない |
| `OVERVIEW_MISSING` | ERROR | `## 概要`がない |
| `OVERVIEW_EMPTY` | ERROR | 概要に本文がない |
| `SOURCE_SECTION_MISSING` | ERROR | `## 外部ソース`がない |
| `SOURCE_SECTION_MULTIPLE` | ERROR | 外部ソース節が複数ある |
| `SOURCE_SECTION_NOT_LAST` | ERROR | 外部ソース節の後にH2がある |
| `HEADING_LEVEL_SKIP` | WARNING | H2からH4など見出しレベルが飛ぶ |
| `DUPLICATE_HEADING` | WARNING | 同一階層に同名見出しが複数ある |

schemaは「必要なセクションだけ使う」としているため、`## 詳細`と`## 関連`は必須にしない。概要の「1〜3文」は機械的に数えられるが、略語や箇条書きで誤判定しうるため、採用する場合もWARNINGに留める。

### C. wikiリンク

| code | 重大度 | 条件 |
|---|---|---|
| `WIKILINK_ALIAS_FORBIDDEN` | ERROR | `[[slug|表示テキスト]]`を使用している |
| `WIKILINK_EMPTY` | ERROR | `[[]]`または空の名前空間・slug |
| `WIKILINK_TARGET_MISSING` | ERROR | 同一コレクションの参照先が存在しない |
| `WIKILINK_COLLECTION_UNKNOWN` | ERROR | `[[col:slug]]`のcolが存在しない |
| `WIKILINK_CROSS_TARGET_MISSING` | ERROR | クロスコレクションの参照先が存在しない |
| `WIKILINK_SLUG_INVALID` | ERROR | 参照slugが命名規則に違反する |
| `WIKILINK_SELF_REFERENCE` | WARNING | 記事が自分自身を参照している |
| `WIKILINK_DUPLICATE_RELATED` | WARNING | 関連節内で同じslugを複数回列挙している |
| `WIKILINK_RELATED_FORMAT` | WARNING | 関連節の項目が`- [[slug]] — 説明`形式でない |

本文で要求される`概念名（[[slug]]）`形式は、すべてのリンク文脈を正しく識別する必要がある。括弧内リンクでないという理由だけでERRORにすると、関連節や表など正当な例外を誤検出するため、初期実装には含めない。将来追加する場合は、Markdown AST上で散文段落だけを対象にしたWARNINGとする。

リンク解析ではコードフェンス、インラインコード、HTMLコメント内の`[[...]]`を除外する。現在のgrepベース検査はこれらを誤検出しうるため、保存時validatorへの集約時に改善する。

### D. 外部ソースと本文参照

既存の`insight_source_validator.py`を正本として再利用し、診断codeだけを次の体系へ整理する。

| code | 重大度 | 条件 |
|---|---|---|
| `SOURCE_SECTION_MISSING` | ERROR | 外部ソース節がない |
| `SOURCE_ENTRY_INVALID` | ERROR | 項目が規定形式に一致しない |
| `SOURCE_ID_DUPLICATE` | ERROR | S IDが重複する |
| `SOURCE_ID_SEQUENCE` | ERROR | S IDがS1からの連番でない |
| `SOURCE_REF_UNKNOWN` | ERROR | 本文の`[Sn]`に対応する項目がない |
| `SOURCE_REF_MALFORMED` | ERROR | `[S 1]`、`[s1]`など誤った参照形式 |
| `SOURCE_TOPIC_FORBIDDEN` | ERROR | 外部ソース節に`topic:`がある |
| `SOURCE_MISSING` | BLOCKING | `外部ソース未確認。`または有効項目なし |
| `SOURCE_UNVERIFIED` | BLOCKING | 一次・二次がなく、参考・要確認だけ |
| `SOURCE_URL_SYNTAX` | ERROR | URLとして記載された値の構文が不正 |
| `SOURCE_ID_UNUSED` | INFO | 本文から参照されないS ID |

`SOURCE_ID_UNUSED`は通常説明の背景資料では正常なので、修正要求にはしない。URL疎通、内容、source分類の妥当性も独自lintでは判定しない。

本文中の`[S1]`は外部ソース節より前だけを対象にする。外部ソースの説明文中に現れたIDを本文参照として数えない。コード、引用した原文、インラインコードも可能なら除外する。

### E. index整合性

indexの正確なフォーマットを先に仕様として固定し、その仕様だけをlintする。形式が未確定のまま正規表現を実装しない。

最低限、次を全体lintで検査する。

| code | 重大度 | 条件 |
|---|---|---|
| `INDEX_ENTRY_TARGET_MISSING` | ERROR | indexが存在しないslugを参照する |
| `INDEX_ENTRY_DUPLICATE` | ERROR | 同じslugが複数回登録されている |
| `INDEX_PAGE_MISSING` | ERROR | 正式なpageがindexに登録されていない |
| `INDEX_TITLE_MISMATCH` | WARNING | indexの表示タイトルが記事タイトルと一致しない |
| `INDEX_SUMMARY_EMPTY` | WARNING | 規定上必要なサマリが空 |

リダイレクトページや統合済みページをindexへ含めるかは、先にschemaで定義する。lintが独自の掲載方針を作ってはならない。

## 診断モデル

各診断は人間向けメッセージだけでなく、少なくとも次の構造を持つ。

```json
{
  "code": "TITLE_H1_MISMATCH",
  "severity": "error",
  "file": "wiki/insight/pages/example.md",
  "line": 7,
  "column": 1,
  "message": "frontmatter titleとH1が一致しません",
  "expected": "期待するタイトル",
  "actual": "現在のH1"
}
```

診断codeはテストとHookの契約になるため、文言変更と切り離して安定させる。出力形式は次の3つを用意する。

- `human`: Claude Codeと手動実行向け
- `json`: Hook、テスト、将来のエディタ統合向け
- `github`: CIの行注釈向け。CIを導入するときに追加してもよい

終了コードは次に固定する。

| code | 意味 |
|---:|---|
| 0 | ERROR/BLOCKINGなし |
| 1 | lint自体の実行エラー、設定不正、読込失敗 |
| 2 | ERRORまたはBLOCKINGを検出 |

WARNINGやINFOだけでは非0にしない。`--fail-on warning`のような切替を追加する場合も、既定値はERRORとする。

## 実装構成

推奨構成は次のとおりである。

```text
.claude/skills/lint/
├── SKILL.md
├── lint-check.sh                  # 全体lintのオーケストレーション
├── insight_validator.py          # 記事単体の入口
├── insight_source_validator.py   # 既存。source検査を提供
├── insight_index_validator.py    # indexとpagesの全体検査
└── test_insight_validators.py

.claude/hooks/
└── lint-insight-after-write.sh   # stdinのHook JSONから対象pathを取り出す薄いwrapper
```

`.agents/`は作らない。スキル定義も増やさず、既存のlintスキル内へ置く。

`insight_validator.py`は次の使い方を想定する。

```bash
python3 .claude/skills/lint/insight_validator.py \
  --format human \
  wiki/insight/pages/example.md
```

複数ファイルを受け付け、対象が`wiki/insight/pages/*.md`でない場合は何もせず成功する。Hook wrapper側とvalidator側の両方で対象範囲を確認し、誤ってwiki全体へ重い検査を走らせない。

frontmatter解析に外部YAMLライブラリを使う場合は、依存関係をリポジトリで固定する。依存を増やさないために独自YAMLパーサを書くことは避ける。許可するfrontmatterが単純でも、引用、日付型、重複keyの扱いを誤る可能性がある。

Markdownについても、文脈を区別する規則はASTを利用する。初期段階で依存を増やしたくない場合は、コードフェンスとfrontmatterを明示的にマスクした小さなscannerから始め、対応範囲をテストで固定する。

## PostToolUse連携

Hookは`Write`と`Edit`の成功後に実行し、tool inputから変更対象のpathを取得する。

処理フローは次のとおり。

```text
Write/Edit完了
  → 対象が wiki/insight/pages/*.md か
    → NO: 終了0
    → YES: insight_validator.pyを対象ファイルだけに実行
      → ERRORなし: 終了0
      → ERRORあり: 診断をClaudeへ返し、修正を促す
```

Hookでは次を実行しない。

- 全ページ走査
- 孤立ページ検査
- リンク漏れ候補探索
- Codex評価
- suikoの文書集合監査
- 外部URLへのHTTPアクセス
- 自動修正

外部リンク検査やCodex評価をPostToolUseへ入れると、保存のたびにネットワーク待ちや高コスト処理が発生する。これらは`/lint`、`/review-page`またはCIへ残す。

同じツール呼び出しの直後にClaudeが修正を繰り返す可能性があるため、Hookのメッセージにはcode、位置、期待値を含め、曖昧な改善依頼を返さない。Hook自身がファイルを書き換えると、意図しない再実行や意味変更を起こすため、検出専用とする。

## 全体lintとの統合

既存の`lint-check.sh`はオーケストレーターとして維持するが、記事単体の構造検査をshellのgrepへ追加し続けない。

全体lintは次の順にする。

1. 全insight記事へ`insight_validator.py`を実行
2. `insight_index_validator.py`を実行
3. コレクション横断のリンク・孤立・リンク漏れ候補を検査
4. 評価状態を検査
5. LLM担当の重複・矛盾・合成機会へ進む

記事単体のERRORがある場合、Codex品質評価へ進めても入力品質が保証されない。少なくとも対象記事の構造ERRORを先に解消し、sourceの`SOURCE_MISSING`または`SOURCE_UNVERIFIED`は既存ルーブリックどおりBlockingとして評価へ伝える。

## 自動修正

初期版は検出専用とする。

将来自動修正してよい候補は、意味を変えず、結果が一意なものに限る。

- frontmatterや行末の余分な空白
- source IDの単純な連番変更。ただし本文参照を同時更新できる場合のみ
- 明白な旧表記から正規表記への置換。ただしこれはprhの責務

次は自動修正しない。

- タイトルとH1のどちらを正とするか
- 壊れたwikiリンクの参照先推測
- source分類の変更
- 外部ソース説明文の生成
- 概要の短縮
- 「AI特有表現」の言い換え

## 段階導入

### Phase 1: 保存条件の固定

- 既存`insight_source_validator.py`の回帰テストを増やす
- frontmatter、H1、概要、外部ソース、wikiリンクを実装する
- 全既存記事へ実行し、現状違反を一覧化する
- 既存違反を直す前は、新規ERRORと既存負債を区別できるbaselineまたは変更ファイル限定運用にする

### Phase 2: PostToolUse導入

- Write/Edit後に変更ファイルだけ検査する
- まず診断表示のみで運用し、誤検知を確認する
- 誤検知のないcodeだけ作業を止めるERRORとして有効化する

### Phase 3: indexと全体整合性

- index形式をschemaで固定する
- index validatorを追加する
- 既存`lint-check.sh`のリンク検査をPython側へ段階的に移す

### Phase 4: 汎用校正ツールとの統合

- 独自lintとは別プロセスでtextlint/prhを実行する
- suikoとAI writing presetはWARNING/INFOとして試験する
- 外部リンクは全体lintまたはCIでlycheeに任せる

独自lintへ表記辞書、AI表現、HTTP検査まで取り込まない。各ツールの責務を分けた方が、誤検知の理由と保守担当を追跡しやすい。

## テスト方針

各診断codeに、最小の正常fixtureと異常fixtureを1つ以上用意する。複数規則を1つの巨大fixtureでまとめて試さない。

特に次の境界条件を固定する。

- frontmatter内の`---`を本文区切りと誤認しない
- CRLF、末尾改行なし、BOMをどう扱うか
- コードフェンス内の`[[missing]]`と`[S99]`を無視する
- インラインコード内のリンク記法を無視する
- `[[it:adr]]`をクロスリンクとして解決する
- URL中の`[S1]`相当文字列を参照と誤認しない
- source説明文中の句点、URL内のピリオドを正しく扱う
- H3以下の「外部ソース」という文字列をH2と誤認しない
- 日本語タイトル、引用符付き日付、YAML重複keyを扱う
- 複数ファイル入力時も診断順が安定する

診断順は`file → line → column → code`などに固定する。連想配列やfilesystem列挙順へ依存すると、Hook出力とテストが不安定になる。

## 採用判断

この独自lintは導入価値が高い。理由は、すでにschemaとして明文化された保存条件が多く、誤検知をほぼ出さずに検査でき、既存実装も相当部分存在するためである。

ただし、価値の中心はルール数ではない。記事保存時に保証すべき不変条件を一か所へ集約し、どの書き込み経路でも同じvalidatorを通すことにある。実装時は、検出可能だからという理由で文体や品質判断まで独自lintへ広げない。

最初に実装する範囲は次で十分である。

1. frontmatter
2. titleとH1
3. 概要と外部ソース節
4. source ID整合性
5. wikiリンク構文と参照先

この5領域が安定してから、index整合性とHookのblocking運用へ進む。
