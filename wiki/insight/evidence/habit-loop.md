# 外部検証記録: habit-loop

独立評価者による外部検証を検証ごとに追記する。過去の節は書き換えない。

## 2026-09-06T15:38:24Z run=6fc7579674c2

- target: wiki/insight/designs/habit-loop.md
- target_blob: cd5c1a9efc424b25333e1458e7c5d1baeecc039a
- evaluator: codex / gpt-5.6-sol
- 移行元: evaluations/insight/habit-loop/external/7b55eb8f0305-external-6fc7579674c2.md（2026-09-25に旧形式から変換）

### 確認済み

- **主張:** James Clear本人のページは、習慣形成を `cue → craving → response → reward` の四段階として提示している。  
  **根拠:** 著者名がJames Clearと明記され、「The Science of How Habits Work」直下で習慣形成をこの四段階に分けると説明している。全習慣が同じ順序で進むとも明記されている。  
  **URL:** [How To Start New Habits That Actually Stick（7–13、29–37行）](https://jamesclear.com/three-steps-habit-change)

- **主張:** 四段階の相互関係は、単なる列挙ではなく因果的なフィードバックループとして直接説明されている。  
  **根拠:** cueがcravingを引き起こし、cravingがresponseを動機づけ、responseがrewardをもたらし、rewardがcravingを満たしてcueとの関連を形成すると要約されている。また、rewardが将来記憶すべき行動を教え、ループを閉じること、四段階のどれかが欠けると習慣の発生・反復が阻害されることも説明されている。  
  **URL:** [同ページ（38–52行）](https://jamesclear.com/three-steps-habit-change)

- **主張:** 四段階は問題フェーズと解決フェーズに分けられる。  
  **根拠:** cueとcravingを「problem phase」、responseとrewardを「solution phase」と明記している。  
  **URL:** [同ページ（53–54行）](https://jamesclear.com/three-steps-habit-change)

- **主張:** James Clearは四段階に対応する「Four Laws of Behavior Change」を直接提示している。  
  **根拠:** 良い習慣について、Cue＝Make it obvious、Craving＝Make it attractive、Response＝Make it easy、Reward＝Make it satisfying と対応づけている。悪い習慣には各法則の反転として invisible / unattractive / difficult / unsatisfying も掲載している。  
  **URL:** [同ページ「Where to Go From Here」（70–93行）](https://jamesclear.com/three-steps-habit-change)

- **主張:** 携帯通知に相当する具体例が直接提示されている。  
  **根拠:** 表の例は、`Your phone buzzes with a new text message`（cue）→内容を知りたい（craving）→携帯を取りメッセージを読む（response）→読みたい欲求が満たされ、携帯を取る行為が振動と関連づく（reward）という四段階である。「一般的な通知」ではなく、厳密には**新しいテキストメッセージによる携帯の振動**の例である。  
  **URL:** [同ページ（56–60行）](https://jamesclear.com/three-steps-habit-change)

- **帰属上の注意:** insight記事では、このページを「James Clearがこの四段階モデルと四法則を提示・説明している」根拠として保持できる。ただし、四段階の用語や図式そのものをClear独自の創始とする帰属は避けるべきである。本人が、用語はCharles Duhigg、図の設計はNir Eyalの影響を受けた組み合わせだと明記し、脚注でもDuhiggの用語を発展させ四法則へ統合したと説明している。  
  **URL:** [同ページ（50–52、99–102行）](https://jamesclear.com/three-steps-habit-change)

### 未確認

- なし。指定された四段階モデル、相互関係、四つの行動変化法則、携帯の例は、いずれも指定のJames Clear本人ページで直接確認できた。

### 誤り

- なし。  
  ただし記事が携帯例を「通知一般」と断定している場合は、一次資料に合わせて「新しいテキストメッセージで携帯が振動する例」と具体化すると正確になる。

## 2026-09-06T15:45:50Z run=c74e4c664b4f

- target: wiki/insight/designs/identity-based-habit-formation.md
- target_blob: cb77bc86cd1712f228117de29a7b4bdaa0abbe08
- evaluator: codex / gpt-5.6-sol
- 移行元: evidence/identity-based-habit-formation.md（2026-09-26、不採用による削除に伴い、習慣の自動性に関する確認だけを移した。自己像に関する項目は移していない）

### 確認済み

主張: 習慣自動性には、同一文脈での行動反復が関係する。  
根拠: Lally et al. は96人に同じ文脈で12週間反復させ、自動性が漸近的に増加したと報告。Wood & Neal は文脈特徴と反応の連合学習として理論化している。URL: https://doi.org/10.1002/ejsp.674 / https://doi.org/10.1037/0033-295X.114.4.843
