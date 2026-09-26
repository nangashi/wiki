# insight記事の総改稿（記事基準v7・設計基準v2）

Gemini執筆記事の正確性修正を起点に、全insight記事を新基準で設計・執筆・独立評価まで通す。フェーズ順に進め、前のフェーズを終えてから次へ移る。

## 前提

- 記事統合TODO（旧0003）は2026-09-25に完了した。統合元の`inu-no-michi`、`local-optimization-trap`、`parallel-path-trap`は削除済み。
- 2026-09-25に記事基準をv7、設計基準をv2へ改定した（概要第1段落、削除候補、想定分量、適用テスト）。このため、v6で評価が現行だった7件（`avoidance-generated-reasons`、`focus-on-contribution`、`issue-value-matrix`、`learning-roi`、`org-productivity-misdiagnosis`、`prospect-theory`、`theory-of-constraints`）を含め、全70記事の記事評価と設計評価が再評価対象になった。
- 同日、評価の置き場を`wiki/insight/evaluations/<slug>/{article,design}.md`（上書き・git追跡）と`wiki/insight/evidence/<slug>.md`（外部検証の追記）へ移した。旧評価はコミット`8c16c45`の`evaluations/insight/`でだけ参照でき、トリアージの材料には使えるが評価者には渡さない。19件の設計が失われた評価記録を参照している（CHECK-9c）。各記事の設計を直すときに参照を`evidence/`へ直すか、設計内で根拠を完結させる。
- 評価は記事・設計と同じコミットに入れる。評価の往復回数は評価ファイルの`round`に残る（フェーズ2の記録に使う）。
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

## フェーズ1: トリアージ（完了・2026-09-25承認）

全70記事をR1・R2と既存記事との重なりで振り分け、49件に絞った。旧評価（v6）はゲートを全件合格としていたため、判定の決め手にせず材料として参照した。統合・削除の実作業はフェーズ3で行う。

- [x] 各記事を維持／統合／不採用に振り分ける
- [x] 統合クラスタとTips・心得型のゲート判定
- [x] ユーザー確認と対象リストへの反映

### 統合（統合元12件 → 統合先11件）

統合先の設計に統合元の独自内容を取り込み、統合元の記事・設計を削除する。統合元の外部検証記録があれば統合先の`evidence/`へ追記してから削除し、統合元への被リンクを統合先へ付け替える。

| 統合元 | 統合先 | 理由 |
|---|---|---|
| liking-principle、authority-principle | cialdini-persuasion-triggers | 独自の機序が薄く、推論が総論の「手掛かりと要求の中身を分ける」とほぼ同じ。authorityの「情報の採用と指示への服従の区別」は総論へ移す。独自の機序を持つ返報性・一貫性・希少性・社会的証明は単独で残す |
| environment-design-behavior | habit-loop | 手がかりと開始の手間という介入点は、習慣ループの「きっかけ」の操作そのもの |
| learning-depth-and-breadth-roles | learning-roi | 深さと広さを目的で選ぶ話はバランス論の型。有用な部分は「目的と必要な到達点」節と重なる |
| learning-deepening-operations | question-generation | 5つの操作は「見えない欠落を露呈させて問いにする」操作に収まる。分類軸の正当化が弱い |
| shin-dokkai | language-context-dependence | どちらも「会話はできるのに説明文を読めない」の説明。RSTの読解技能を読解が止まる箇所の診断に使う |
| community-of-knowledge | illusion-of-explanatory-depth | 同じ著者。参照できる知識を自分の理解と取り違えることは、説明深度の錯覚の原因の説明にあたる |
| attention-residue | interruption-recovery-cost | 同じ中断の前後の局面。両記事とも相手との違いの説明に1節を使っている |
| pre-analysis-output-design | hypothesis-as-stance | 絵コンテは、仮説から集める情報と答えの形を先に決めることの適用 |
| time-record-organize-consolidate | quadrant-ii-principle | どちらも重要で緊急でない仕事の時間を守る判断。記録と連続時間の確保はその手段 |
| knowledge-worker-autonomy | focus-on-contribution | 課題の定義を本人と確かめることは、貢献への集中を管理者側から見たもの |
| nonviolent-communication | needs-vs-strategies | ニーズと手段の区別がNVCで最も再利用できる核。「依頼と要求の区別」を移す |

### 不採用（9件）

記事・設計を削除し、被リンクを削除または付け替える。

| 記事 | 理由 |
|---|---|
| character-ethics-vs-personality-ethics | 規範的な主張で、推論を変える構造がない |
| maturity-continuum | 価値観の主張。責任の所在の点検はfocus-on-controllableと重なる |
| stimulus-response-freedom | 経験的な機序ではなく哲学的な枠組み |
| plateau-of-latent-potential | 核心が比喩。練習の質の点検は一般論にとどまる |
| identity-based-habit-formation | 外部検証で、自己像が反復より効くという主張は未確認。機序が薄い |
| problem-driven-selection | Tips。出典は個人の振り返り1件 |
| productivity-layer-model | 層の間で改善が伝わらない構造はtheory-of-constraintsとproxy-metrics-knowledge-workで扱える。6層は講演資料固有の分類 |
| child-activity-redesign | 再利用できる構造はneeds-vs-strategiesの適用例。残りは子育て固有のTips |
| child-communication-principles | 問い・説明・実演を状況で使い分けるバランス論の型 |

### 核心の置き直し（承認済み）

- forgetting-curve: 実験の紹介から、再利用できるモデルである分散学習（間隔効果）へ核心を移し、忘却曲線は背景にする。slug・タイトルの変更は設計時に案を示して確認する。
- conclusion-first-communication: 手法の紹介から、「聞き手は問いと答えの枠組みがないと個々の情報の役割を判断できない」という理解の機序へ核心を移す。根拠を確保できなければ不採用に切り替える（その時点で確認する）。

## フェーズ2: パイロット（3件）

新基準で設計→設計評価→執筆→記事評価→修正→再評価を通し、基準の運用上の問題を洗い出す。

- [x] peak-end-rule
- [x] framing-effect
- [x] forgetting-curve → spacing-effect（核心を分散学習へ移し、slug・タイトルを「分散学習（間隔効果）」へ改名。2026-09-26承認）
- [x] 各記事の評価往復回数、最終字数と想定分量の比、適用テストの結果、事実確認で見つかった誤りを記録する
### パイロット記録

| 記事 | 設計の往復 | 記事の往復 | 本文字数／想定 | 適用テスト | 事実確認で見つかった誤り |
|---|---|---|---|---|---|
| peak-end-rule | 2（Codex 2回、外部検証1回） | 2（形式不正で破棄した評価1回を除く） | 約2,850字／約3,400字 | 3回の第一段階すべてで期待する推論に到達 | S8の書誌（題名・頁、editorが自分の知識で補った箇所）。ほかに「事後評価」の向きの不一致（破棄した評価が指摘し、メインエージェントが確認して修正） |
| framing-effect | 2（Codex 2回、外部検証なし） | 2 | 約2,590字／約3,000字 | 2回の第一段階とも期待する推論の中心に到達（両立する比較基準の検出、不足情報の特定、保留） | 本文の誤りなし。損失側の説明に比較の基準（1.5倍）が欠けていた（論理の修正必須）。S4への「三段階」の帰属とS5の頁を任意改善で直した |
| spacing-effect | 3（先行の外部検証1回、Codex 3回） | 3 | 約3,640字／約5,000〜6,000字 | 3回の第一段階すべてで到達（分割方式の優位予測、複雑課題での断定保留、遅延・実務課題での確認。RIの起点のずれまで指摘） | S4の長期研究の比較対象を誤要約（「一日にまとめる」→正しくは「一日間隔」）。設計評価の任意改善の文案を未検証のまま採用したのが原因で、設計・記事の両方を直した。処理不足説への[S6]の誤帰属（任意改善だったが帰属の誤りなので直した） |

運用上の気づき（フェーズ2の終わりにまとめて判断する）:

- 設計が長い。peak-end-ruleは4.7KB→11KB→16KBになった。本文の書き下ろしはないが、主張表と「言わないこと」が厚く、本文（約8.5KB）の約2倍になった。
- 設計に適用テストの期待する推論があり、editorがそれを一般的な手順として本文に書いた（メインエージェントが削除した）。editorへ渡す設計から期待する推論を伏せるか、執筆指示で禁じる必要がある。
- editorが外部ソースの書誌（巻号・頁・題名）を自分の知識で補い、1件誤った。書誌は設計か外部検証記録にあるものだけを使わせるか、評価の事実確認に必ず含める。
- 第二段階で評価者が`## 記事単独読解`に補足の段落を入れ、形式不正になった。プロトコルの「誤読の訂正は後段に記す」が曖昧で、依頼文で「補足は観点別評価の根拠に書く」と明示すると解消した。プロトコルの文言を直す候補。
- 削除候補に位置（`（27行）`）を添える書き方をvalidatorが拒否した。作業を止める不具合としてvalidatorを直し、プロトコルに許容を追記した（2026-09-25）。
- 第一段階の回答の後にファイルパスの行が付いたことがある。5行だけを保存した。
- 評価者によって指摘がぶれる。破棄した評価は「事後評価」の向きを修正必須にしたが、再試行の評価は指摘しなかった。
- 削除候補のうち、設計が採用を指定した箇所（S7の段落、第3節の判断への接続）はメインエージェントが不採用にした。評価者は設計の採否を知ったうえで削除候補を挙げるので、設計との衝突を毎回判断することになる。
- framing-effectでは、editorへ渡す設計から適用テストの行を除き、書誌を設計にあるものだけに限った。本文への推論の漏れも書誌の補完も起きず、適用テストは本文の一般的な規則からの転用で到達した。書誌を設計でそろえる必要があるため、設計評価で書誌の誌名・リンクの不足を任意改善として拾い、設計修正に含めた。
- 設計に「記事本文より長くしない」と依頼すると、7.8KB（本文約7.5KB）に収まった。
- framing-effectでも削除候補3件がすべて設計の指定する留保・境界と衝突し、不採用にした。2記事で採用できた削除候補は1件だけである。
- 評価者の出力末尾に「確認に使った資料」などの行が付くことがある。設計評価のvalidatorは良い点の節で許容したため、そのまま保存した。記事評価の依頼文には「最後に行を足さない」と書き、再発しなかった。
- 核心を置き直す記事（spacing-effect）では、設計の前に外部検証で根拠を確かめてから設計させた。検証が依頼文の例示の誤り（最適比率「1週間で20〜40%」）を見つけ、設計に入る前に防げた。
- 評価者が任意改善で示した文案（「一日にまとめるより週・月単位に分ける方が有利」）を、原典と照合しないまま設計の修正に採用し、誤要約が設計と記事へ伝わった。評価者の文案は検証済みの事実ではない。採用するときは外部検証記録か原典で確かめる。
- 想定分量は大きく外れることがある（spacing-effectは設計5,000〜6,000字に対し本文約3,640字）。不足ではなかったので、想定分量は上限の目安として扱えば足りる。
- 記事の往復が上限の3巡に達した。任意改善のうち帰属の誤りを直すために1巡使ったため。誤帰属は任意改善ではなく事実基盤の修正必須に分類されるべきで、評価者の分類がぶれている。
- 残った任意改善（spacing-effect）: 「どれも」の係り先、S5の比率の分母（「遅延」→保持間隔）、S7の「テスト結果を見た後でも」の表現確認。フェーズ4の`/lint`で扱う。

- [x] 記録から基準・手順の調整が必要か判断し、必要なら一度だけ改定する。以後フェーズ4まで基準・手順を変えない（作業を止める不具合を除く）。気づいた点は`todos/`へ記録する
  - 2026-09-26に改定済み（基準のversionは据え置き）: editorへの依頼（適用テストを伏せる、書誌は設計に限る、設計にない例・手順を足さない）、評価者の文案の検証、削除候補から設計指定の唯一の記述を除く、誤帰属・書誌誤りを修正必須に明示、記事単独読解への補足の禁止、依頼文の定型（`references/evaluator-requests.md`）、報告の取り出しツール（`tools/extract_agent_report.py`）、Codexへの設計の簡潔さ指示、核心を置き直す記事での設計前の外部検証。以後フェーズ4まで基準・手順を変えない（作業を止める不具合を除く）。

## フェーズ3: 量産（クラスタ単位）

indexのカテゴリまたは統合クラスタを1バッチとし、バッチごとにコミットする。関連欄では、紛らわしい隣接モデル（例: 利用可能性ヒューリスティックとWYSIATI、アンカリングとフレーミング、commitment-and-consistencyとcommitment-lock-in）との見分けを優先する。

優先順:

1. 不採用9件の削除（上表）
2. 統合を含むクラスタ（下記E）
3. 下記A（Gemini執筆）の残り。帰属の創作が起こりやすいため、数値・書誌・DOI・S IDへの帰属をevaluatorの事実確認で照合する
4. 下記C（外部ソースが要確認・参考だけの記事）。一次・二次を確保できなければ不採用を検討し、確認を取る
5. 下記B（`0b15416`）。`/review-page`で設計整合と事実を確認し、必要な箇所だけ直す。重大な逸脱があれば改稿へ切り替える
6. 下記D（v6で評価済み）。新基準で設計を見直し、削除候補を中心に改稿・再評価する

方針（旧TODOから継続）:

- `2fffc44`・`0784ff3`の記事は、現行本文を土台にせずdesignから改めて執筆する（Opus／editor）。旧本文と現行本文の主張を引き継がない。
- 各記事の着手前にdesignを確認し、欠落や誤りがあれば設計手順で先に直す。全記事で設計に想定分量と適用テストを加える（設計基準v2）。
- 後続コミットで手直しされた記事（`fact-interpretation-action`、`focus-on-contribution`、`needs-vs-strategies`、`prospect-theory`は`457eb64`）は、その変更意図をdesignと照合してから扱う。

### 0. 不採用の削除（9件）

- [ ] character-ethics-vs-personality-ethics
- [ ] maturity-continuum
- [ ] stimulus-response-freedom
- [ ] plateau-of-latent-potential
- [ ] identity-based-habit-formation（外部検証記録`evidence/identity-based-habit-formation.md`のうち習慣の自動性に関する確認はhabit-loopの`evidence/`へ追記してから削除する）
- [ ] problem-driven-selection
- [ ] productivity-layer-model
- [ ] child-activity-redesign
- [ ] child-communication-principles

### E. 統合先の改稿（11件、統合元は上表）

- [ ] cialdini-persuasion-triggers（← liking-principle、authority-principle）
- [ ] habit-loop（← environment-design-behavior）
- [ ] learning-roi（← learning-depth-and-breadth-roles）
- [ ] question-generation（← learning-deepening-operations）
- [ ] language-context-dependence（← shin-dokkai）
- [ ] illusion-of-explanatory-depth（← community-of-knowledge）
- [ ] interruption-recovery-cost（← attention-residue）
- [ ] hypothesis-as-stance（← pre-analysis-output-design）
- [ ] quadrant-ii-principle（← time-record-organize-consolidate）
- [ ] focus-on-contribution（← knowledge-worker-autonomy）
- [ ] needs-vs-strategies（← nonviolent-communication）

### A. designから改稿（2fffc44・0784ff3の残り、18件）

- [ ] commitment-lock-in
- [ ] commitment-and-consistency
- [ ] conclusion-first-communication（核心の置き直しを含む）
- [ ] echo-chamber
- [ ] elaborative-interrogation
- [ ] exit-criteria-first
- [ ] fact-interpretation-action
- [ ] feedback-analysis
- [ ] focus-on-controllable
- [ ] identity-foreclosure
- [ ] interleaving
- [ ] knowledge-externalization
- [ ] method-problem-visibility
- [ ] motivated-reasoning
- [ ] motivational-questioning
- [ ] process-praise
- [ ] prospect-theory
- [ ] proxy-metrics-knowledge-work

### C. 未改稿の記事（旧0002の残り、8件）

- [ ] reciprocity-principle
- [ ] scarcity-principle
- [ ] social-proof
- [ ] survivorship-bias
- [ ] system1-system2
- [ ] testing-effect
- [ ] unlearn
- [ ] working-memory-capacity

### B. レビューで修正（0b15416の残り、5件）

- [ ] anchoring-effect
- [ ] availability-heuristic
- [ ] fluency-illusion
- [ ] planning-fallacy
- [ ] wysiati

### D. v6評価済み（4件）

focus-on-contributionとlearning-roiはE、prospect-theoryはAで扱う。

- [ ] avoidance-generated-reasons
- [ ] issue-value-matrix
- [ ] org-productivity-misdiagnosis
- [ ] theory-of-constraints

## フェーズ4: 横断の仕上げ

- [ ] `/lint`で被リンク0・1件の記事、見分けリンク、indexの要約、公開ゲートの通過、孤立記録（CHECK-9d）を確認する
- [ ] indexのカテゴリのずれを直す（focus-on-controllable、quadrant-ii-principleが「教育・子育て」にある。統合・削除後の空カテゴリも整理する）
- [ ] パイロットと量産の記録（評価往復回数、字数）を比べ、`/retrospect`で手順を見直す
- [ ] このTODOを削除する

## 完了条件

- 各記事は、insightの手順に従って検査・独立評価・必須修正・再評価・index更新まで終えてからチェックする。統合・不採用になった記事は、その処理を終えた時点でチェックする。
- 全対象の完了後、このTODOファイルを削除する。

実行時は`/review-page`または`/lint`から対象wikiの現行手順へ進む。このTODOは引き継ぎ用であり、設計・執筆・独立評価・公開の手順を置き換えない。
