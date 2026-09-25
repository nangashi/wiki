# insight記事の総改稿（記事基準v7・設計基準v2）

Gemini執筆記事の正確性修正を起点に、全insight記事を新基準で設計・執筆・独立評価まで通す。フェーズ順に進め、前のフェーズを終えてから次へ移る。

## 前提

- 記事統合TODO（旧0003）は2026-09-25に完了した。統合元の`inu-no-michi`、`local-optimization-trap`、`parallel-path-trap`は削除済み。
- 2026-09-25に記事基準をv7、設計基準をv2へ改定した（概要第1段落、削除候補、想定分量、適用テスト）。このため、v6で評価が現行だった7件（`avoidance-generated-reasons`、`focus-on-contribution`、`issue-value-matrix`、`learning-roi`、`org-productivity-misdiagnosis`、`prospect-theory`、`theory-of-constraints`）を含め、全70記事の記事評価と設計評価が再評価対象になった。
- 同日から`evaluations/insight/<slug>/`をgitで追跡する。19件の設計が、それ以前に失われた評価記録を参照している（CHECK-9c）。各記事の設計を直すときに参照を外し、設計内で根拠を完結させる。
- 統合で関連欄だけを付け替えた6記事（`pre-analysis-output-design`、`proxy-metrics-knowledge-work`、`quadrant-ii-principle`、`commitment-lock-in`、`problem-driven-selection`、`productivity-layer-model`）は、本文未変更・独立評価未実施のまま対象に含まれる。

## 調査結果（2026-09-25）

Gemini執筆のコミット`0b15416`（16件）、`0784ff3`（6件）、`2fffc44`（43件）から7件を抽出し、designを正として本文を照合した。外部ソース本体は取得していない。数値は既知の一次文献との照合による。

| 記事 | コミット | 判定 | 主な問題 |
|---|---|---|---|
| peak-end-rule | 2fffc44 | 重大 | designが禁じた「累積苦痛が増加した」「決定を参照するのは記憶する自己」を断定。再受診率の調整条件を欠く。核の冷水実験（S6）が欠落。designが省くとしたピーク演出を適用の中心に置く |
| framing-effect | 2fffc44 | 中 | 属性フレーミングの「赤身90%／脂肪分10%」をS5に帰属（原典の例は75%/25%）。価値関数・確率の重みによる説明節が欠落。誤字「表現表現」 |
| forgetting-curve | 2fffc44 | 中 | S4のDOIを`0033-295X`へ改変（正しくは`10.1037/0033-2909.132.3.354`）。「間隔を段階的に広げる」「望ましい困難が原因」をS4に帰属（designは検索努力の単一原因説明を省略） |
| habit-loop | 2fffc44 | 軽微 | Lallyの66日は中央値だが「平均」と記載。範囲「254日以上」も不正確 |
| commitment-lock-in | 0784ff3 | 軽微 | S3のURL（著者公開の補完資料`linux.pdf`）に書名『Information Rules』（1999）を付与した疑い（未取得）。「他のすべての補完要素を再構築」と過度に一般化 |
| theory-of-constraints | 0b15416 | 良好 | designにほぼ忠実（0003で改稿） |
| interruption-recovery-cost | 0b15416 | 良好 | 数値・境界ともdesignに忠実 |

誤りの型:

1. designが旧本文の誤りを訂正していても、Geminiが旧本文の主張へ戻る（peak-end-ruleで確認）。
2. 出典にない具体的な数値・知見・書名を、既存のS IDに帰属させる。自然に読めるため通読では気づきにくい。
3. DOI等の識別子を改変する。
4. designの必須の節・到達点を落とす。

`evaluations/insight/peak-end-rule/`には`design/`しかなく、記事の独立評価は未実施だった。他のGemini記事も記事評価を経ていない前提で扱う。

## フェーズ1: トリアージ（記事を書かない）

全70記事を概要・設計・再利用性基準で振り分け、以後の作業量を確定する。統合・削除・別コレクションへの移動は、一覧表でユーザー確認を取ってから行う。

- [ ] 各記事を「維持／統合（統合先）／不採用（削除・移動先）／軽い修正」に振り分けた一覧を作る。判定理由はR1・R2と既存記事との重なりで書く
- [ ] 統合候補のクラスタを検討する（例: Cialdini系7件〔`cialdini-persuasion-triggers`と各原理6件〕、習慣系〔`habit-loop`、`identity-based-habit-formation`、`environment-design-behavior`、`plateau-of-latent-potential`〕）
- [ ] Tips・心得型の疑いがある記事のゲート判定（例: `conclusion-first-communication`、`learning-depth-and-breadth-roles`、`child-activity-redesign`、`child-communication-principles`）
- [ ] 一覧をユーザーに確認し、承認された統合・不採用を下の対象リストへ反映する

## フェーズ2: パイロット（3件）

新基準で設計→設計評価→執筆→記事評価→修正→再評価を通し、基準の運用上の問題を洗い出す。

- [ ] peak-end-rule
- [ ] framing-effect
- [ ] forgetting-curve
- [ ] 各記事の評価往復回数、最終字数と想定分量の比、適用テストの結果、事実確認で見つかった誤りを記録する
- [ ] 記録から基準・手順の調整が必要か判断し、必要なら一度だけ改定する。以後フェーズ4まで基準・手順を変えない（作業を止める不具合を除く）。気づいた点は`todos/`へ記録する

## フェーズ3: 量産（クラスタ単位）

indexのカテゴリまたは統合クラスタを1バッチとし、バッチごとにコミットする。関連欄では、紛らわしい隣接モデル（例: 利用可能性ヒューリスティックとWYSIATI、アンカリングとフレーミング）との見分けを優先する。

優先順:

1. 統合を含むクラスタ
2. 下記A（Gemini執筆）の残り。帰属の創作が起こりやすいため、数値・書誌・DOI・S IDへの帰属をevaluatorの事実確認で照合する
3. 下記C（外部ソースが要確認・参考だけの13件）。一次・二次を確保できなければフェーズ1に戻して不採用を検討する
4. 下記B（`0b15416`）。`/review-page`で設計整合と事実を確認し、必要な箇所だけ直す。重大な逸脱があれば改稿へ切り替える
5. v6で評価済みだった7件（上記前提）。新基準で設計を見直し、削除候補を中心に改稿・再評価する

方針（旧TODOから継続）:

- `2fffc44`・`0784ff3`の記事は、現行本文を土台にせずdesignから改めて執筆する（Opus／editor）。旧本文と現行本文の主張を引き継がない。
- 各記事の着手前にdesignを確認し、欠落や誤りがあれば設計手順で先に直す。
- 後続コミットで手直しされた記事（`fact-interpretation-action`、`focus-on-contribution`、`needs-vs-strategies`、`prospect-theory`は`457eb64`）は、その変更意図をdesignと照合してから扱う。

### A. designから改稿（2fffc44・0784ff3）

優先（重大・中の逸脱を確認済み）:

- [ ] peak-end-rule
- [ ] framing-effect
- [ ] forgetting-curve

その他:

- [ ] habit-loop
- [ ] commitment-lock-in
- [ ] commitment-and-consistency
- [ ] conclusion-first-communication
- [ ] echo-chamber
- [ ] elaborative-interrogation
- [ ] environment-design-behavior
- [ ] exit-criteria-first
- [ ] fact-interpretation-action
- [ ] feedback-analysis
- [ ] focus-on-contribution
- [ ] focus-on-controllable
- [ ] hypothesis-as-stance
- [ ] identity-based-habit-formation
- [ ] identity-foreclosure
- [ ] interleaving
- [ ] knowledge-externalization
- [ ] knowledge-worker-autonomy
- [ ] language-context-dependence
- [ ] learning-deepening-operations
- [ ] learning-depth-and-breadth-roles
- [ ] liking-principle
- [ ] maturity-continuum
- [ ] method-problem-visibility
- [ ] motivated-reasoning
- [ ] motivational-questioning
- [ ] needs-vs-strategies
- [ ] nonviolent-communication
- [ ] plateau-of-latent-potential
- [ ] pre-analysis-output-design
- [ ] problem-driven-selection
- [ ] process-praise
- [ ] productivity-layer-model
- [ ] prospect-theory
- [ ] proxy-metrics-knowledge-work

### B. レビューで修正（0b15416）

- [ ] anchoring-effect
- [ ] attention-residue
- [ ] authority-principle
- [ ] availability-heuristic
- [ ] character-ethics-vs-personality-ethics
- [ ] child-activity-redesign
- [ ] child-communication-principles
- [ ] cialdini-persuasion-triggers
- [ ] community-of-knowledge
- [ ] fluency-illusion
- [ ] illusion-of-explanatory-depth
- [ ] interruption-recovery-cost
- [ ] planning-fallacy
- [ ] wysiati

### C. 未改稿の記事（旧0002の残り、Opusで執筆）

旧TODO 0002でGeminiによる改善を予定していた`quadrant-ii-principle.md`以降（ファイル名の昇順）のうち、上記と0003に含まれない記事。

- [ ] quadrant-ii-principle
- [ ] question-generation
- [ ] reciprocity-principle
- [ ] scarcity-principle
- [ ] shin-dokkai
- [ ] social-proof
- [ ] stimulus-response-freedom
- [ ] survivorship-bias
- [ ] system1-system2
- [ ] testing-effect
- [ ] time-record-organize-consolidate
- [ ] unlearn
- [ ] working-memory-capacity

### D. v6評価済みの7件

- [ ] avoidance-generated-reasons
- [ ] focus-on-contribution（Aにも掲載。Aで扱えばここも完了とする）
- [ ] issue-value-matrix
- [ ] learning-roi
- [ ] org-productivity-misdiagnosis
- [ ] prospect-theory（Aにも掲載。Aで扱えばここも完了とする）
- [ ] theory-of-constraints

## フェーズ4: 横断の仕上げ

- [ ] `/lint`で被リンク0・1件の記事、見分けリンク、indexの要約、公開ゲートの通過を確認する（`nonviolent-communication`は評価を通るまでindexから外れている）
- [ ] パイロットと量産の記録（評価往復回数、字数）を比べ、`/retrospect`で手順を見直す
- [ ] このTODOを削除する

## 完了条件

- 各記事は、insightの手順に従って検査・独立評価・必須修正・再評価・index更新まで終えてからチェックする。統合・不採用になった記事は、その処理を終えた時点でチェックする。
- 全対象の完了後、このTODOファイルを削除する。

実行時は`/review-page`または`/lint`から対象wikiの現行手順へ進む。このTODOは引き継ぎ用であり、設計・執筆・独立評価・公開の手順を置き換えない。
