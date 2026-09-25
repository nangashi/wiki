# Gemini執筆記事の正確性修正とOpusによる改稿

## 前提

[記事統合TODO](0003-reassess-article-integration.md)の完了後に着手する。0003で統合・補修する次の記事はこのTODOの対象から除く。

- 統合元として削除: `inu-no-michi`、`local-optimization-trap`、`parallel-path-trap`
- 統合先・補修先として改稿済み: `issue-value-matrix`、`theory-of-constraints`、`avoidance-generated-reasons`、`learning-roi`、`org-productivity-misdiagnosis`

着手時に0003の完了を確認する。未完了なら、上記の記事に触れる作業を0003と重複させない。

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

## 方針

- `2fffc44`・`0784ff3`の記事は、現行本文を土台にせずdesignから改めて執筆する（Opus／editor）。旧本文と現行本文の主張を引き継がない。
- `0b15416`の記事は抽出した範囲では正確だったため、`/review-page`でdesign整合と事実を確認し、必要な箇所だけ修正する。重大な逸脱が見つかれば改稿へ切り替える。
- 本文の数値・書誌・DOI・S IDへの帰属はevaluatorの事実確認で照合する。執筆モデルを替えても帰属の創作は起こりうるため、独立評価を省かない。
- 各記事の着手前にdesignを確認し、欠落や誤りがあれば設計手順で先に直す。
- 後続コミットで手直しされた記事（`fact-interpretation-action`、`focus-on-contribution`、`needs-vs-strategies`、`prospect-theory`は`457eb64`）は、その変更意図をdesignと照合してから扱う。

## 対象記事

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

## 完了条件

- 各記事は、insightの手順に従って検査・独立評価・必須修正・再評価・index更新まで終えてからチェックする。
- 全対象の完了後、このTODOファイルを削除する。

実行時は`/review-page`から対象wikiの現行手順へ進む。このTODOは引き継ぎ用であり、設計・執筆・独立評価・公開の手順を置き換えない。
