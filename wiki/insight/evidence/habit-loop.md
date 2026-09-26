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

## 2026-09-26T06:27:25Z run=habitloopmergeext1

- target: wiki/insight/designs/habit-loop.md
- target_blob: e900f909ae324cb480ad5e547ce46d5c91dfc3e1
- evaluator: claude / opus

### 確認済み

- A1 書誌 / PDFの1頁冒頭とCrossrefで一致。Lally, P., van Jaarsveld, C. H. M., Potts, H. W. W., & Wardle, J.、"How are habits formed: Modelling habit formation in the real world"、European Journal of Social Psychology 40(6), 998–1009、DOI 10.1002/ejsp.674。オンライン公開は2009年7月16日、巻号は2010年。号「6」はPDFに印字がなくCrossrefで確認した / https://api.crossref.org/works/10.1002/ejsp.674 ; https://emotionalfirstaidacademy.com/wp-content/uploads/2023/10/How-habits-are-formed.pdf
- A2 参加者数と分析対象 / p.1000 Method: 説明会に来た101人のうち96人が参加。p.1001–1002: 96人（男30・女66、主に大学院生）。60日目以降にデータを入れなかった14人を脱落とし、分析対象は82人。モデルが当てはまったのは62人、よく当てはまった（R²≥.7、漸近線≤49）のは39人（82人の48%） / 同PDF
- A2 期間と行動の選び方 / 抄録「chose an eating, drinking or activity behaviour to carry out daily in the same context (for example 'after breakfast') for 12 weeks」。p.1000: 健康的な飲食・運動の行動を自分で選ぶ。条件は、まだしていない行動で、1日1回だけ起きる日常の出来事（cue）に続けて行えること。84日間毎日行う。内訳は飲食（eating）27人、飲料（drinking）31人、運動34人、その他4人（p.1001） / 同PDF
- A2 自動性の測定 / p.1001 Measures: Self-Report Habit Index（SRHI; Verplanken & Orbell, 2003）。12項目・7件法のうち、頻度と自己同一性の項目を除いた7項目（2,3,5,6,8,9,10）で自動性の下位尺度を作った（得点範囲0–42）。毎日自己報告する方式 / 同PDF
- A3 代表値は中央値で66日 / p.1002「The median time to reach 95% of asymptote was 66 days, with a range from 18 to 254 days」。Table 2（p.1004、N=39）は中央値66、四分位39:102、最小18、最大254。対象は82人全体ではなく、よく当てはまった39人だけ / 同PDF
- A3 範囲にはモデルの予測（外挿）が含まれる / 観察は84日（p.1000）で、最大値254日はこれを超える。254日は観測値ではなく、Mitscherlich曲線の定数から「-ln(a/20b)/c」で計算した値（p.1001）。Discussion（p.1007）の表現も「average modelled time to plateau」。観察期間を超える部分が外挿だというのは、この二点からの推論で、論文に「extrapolate」という語はない / 同PDF
- A4 1日の実行を逃しても形成はほとんど損なわれない / 抄録「Missing one opportunity to perform the behaviour did not materially affect the habit formation process」。p.1006: 55人に140回の実行漏れがあった。漏れた直後の低下は平均0.29点で有意差なし。3日連続で実行した場合の上昇0.79点に対し、漏れを挟んだ場合は0.55点。p.1007は1回の漏れと、1週間単位の中断（Armitage, 2005）は別物だと区別している / 同PDF
- A5 行動の種類による違いの記述はある。ただし有意差はない / p.1006: 95%到達日数の中央値は飲食65、飲料59、運動91（p=.328、有意差なし）。漸近線は34、35、35（p=.708）。p.1007「the exercise group took one and a half times longer to reach their asymptote」。ただし下位集団を比べる検出力がなく、結論は出せないと明記している / 同PDF
- B1 書誌 / Neal, D. T., Wood, W., & Quinn, J. M. (2006). "Habits—A Repeat Performance." Current Directions in Psychological Science 15(4), 198–202。PDFの198頁とCrossrefで一致 / https://api.crossref.org/works/10.1111/j.1467-8721.2006.00435.x ; https://dornsife.usc.edu/wendy-wood/wp-content/uploads/sites/183/2023/10/Neal.Wood_.Quinn_.2006_Habits_a_repeat_performance.pdf
- B2 文脈の手がかりと反応の結びつき / 抄録「Habits are response dispositions that are activated automatically by the context cues that co-occurred with responses during past performance」。p.198: 反応と文脈が時間的・空間的に一緒に起きると連合ができる（「contexts come to cue responses」）。直接手がかり型のモデルでは「merely perceiving a context triggers associated responses」 / 同PDF
- B3 意図とは比較的独立に起こる / p.200: 習慣が強い学生は意図にかかわらず過去の行動を繰り返した（Ji Song & Wood, 2006）。「habitual responding can be cued independently of people's intentions」。意図を変える介入は、反復で習慣になる行動には効果が小さかった（Webb & Sheeran, 2006）。p.201 結論「habits keep us doing what we have always done, despite our best intentions to act otherwise」 / 同PDF
- B4 文脈が変わると崩れる / p.200とFig.2（p.201）: Wood, Tam, & Guerrero Witt (2005)。大学を移った学生で、運動・新聞・テレビの習慣を調べた。文脈が変わると強い習慣も自動的には引き起こされなくなり、意図があるときだけ続いた（「context change disrupted performance of strong habits」）。紹介されているのは転学（新しい大学への移動）の研究で、引っ越し一般の研究ではない / 同PDF
- C1 題名と著者 / 題名は「How To Start New Habits That Actually Stick」、著者はJames Clear / https://jamesclear.com/three-steps-habit-change
- C2 四段階とFour Laws / 「cue, craving, response, reward」の四段階が説明されている。良い習慣には「Make it obvious / attractive / easy / satisfying」をそれぞれcue・craving・response・rewardに対応させる。悪い習慣を断つにはこれを逆にする（invisible, unattractive, difficult, unsatisfying） / https://jamesclear.com/three-steps-habit-change
- D1 題名と出典 / このURLのページ題名は「How to Stick With Good Habits Even When Your Willpower is Gone」で、著者はJames Clear。「This article is an excerpt from Chapter 6 of my New York Times bestselling book Atomic Habits」と明記されている / https://jamesclear.com/choice-architecture
- D2 手がかりを目に見える場所に置く / 例は原文どおり次の四つ。「put your pill bottle directly next to the faucet on the bathroom counter」「place your guitar stand in the middle of the living room」「keep a stack of stationery on your desk」「fill up a few water bottles each morning and place them in common locations around the house」。原則として「If you want to make a habit a big part of your life, make the cue a big part of your environment.」「Make sure the best choice is the most obvious one.」 / https://jamesclear.com/choice-architecture
- D3 病院カフェテリアの数値と出典 / Massachusetts General HospitalのAnne Thorndikeらによる6か月の研究。レジ横の冷蔵庫に水を加え、食品売り場の横に水のボトルのかごを置いた。「soda sales at the hospital dropped by 11.4 percent」「sales of bottled water increased by 25.8 percent」。脚注1の書誌はThorndike et al., "A 2-Phase Labeling and Choice Architecture Intervention to Improve Healthy Food and Beverage Choices," American Journal of Public Health 102, no. 3 (2012), doi:10.2105/ajph.2011.300391 / https://jamesclear.com/choice-architecture
- E1 題名と著者 / このURLのページ題名は「How to Make Your Future Habits Easy」で、著者はJames Clear / https://jamesclear.com/reset-the-room
- E2 次の行動のための準備 / 原文の例は「Want to draw more? Put your pencils, pens, notebooks, and drawing tools on top of your desk, within easy reach.」「Want to exercise? Set out your workout clothes, shoes, gym bag, and water bottle ahead of time.」「Want to improve your diet? Chop up a ton of fruits and vegetables on weekends and pack them in containers...」 / https://jamesclear.com/reset-the-room
- E3 望ましくない行動の手間を増やす / 原文の例は「Unplug the television and take the batteries out of the remote after each use, so it takes an extra ten seconds to turn it back on」。ほかに、昼までスマートフォンを別の部屋に置く、ビールを冷蔵庫の奥に隠す、という例がある / https://jamesclear.com/reset-the-room
- E4 深刻な問題への限界 / 原文「These tricks are unlikely to curb a true addiction, but for many of us, a little bit of friction can be the difference between sticking with a good habit or sliding into a bad one.」 / https://jamesclear.com/reset-the-room

### 未確認

- D2「果物を目立つ場所に置く」という例 / 取得したchoice-architectureのページ本文では、fruitやappleへの言及が見つからなかった（取得ツールの抽出結果による）。食べ物の例は、クッキーやドーナツが目に入ると食べてしまう、という逆向きのものだけだった。『Atomic Habits』本体に果物の例があるかどうかは確かめていない / 記事でこのページを出典にするなら、上の原文の例（薬瓶、ギター、水のボトル）を使う。果物の例を使うなら、書籍の該当頁で確かめる
- D3 Thorndikeらの原論文の頁と、数値の期間の内訳 / 確認できたのはJames Clearの脚注の書誌と数値だけで、AJPH論文そのものは取得していない / 数値を記事に書くなら、AJPH 102(3)の原論文（doi:10.2105/ajph.2011.300391）で数値と頁を確かめる

### 誤り

- 「自動性が頭打ちになるまでの日数は平均約66日」 / 66日は平均ではなく中央値（p.1002本文、Table 2 p.1004）。しかも対象は82人全体ではなく、曲線がよく当てはまった39人だけ。Discussion（p.1007）にも「average modelled time」という表現はあるが、統計量としては中央値 / 修正例は「曲線がよく当てはまった39人で、漸近線の95%に達するまでの日数の中央値は66日（モデルによる推定）」 / https://emotionalfirstaidacademy.com/wp-content/uploads/2023/10/How-habits-are-formed.pdf
- 「18日から254日以上」 / 論文の範囲は「from 18 to 254 days」で、254は最大値（Table 2 Maximum 254）。「以上」を付ける根拠はない。また84日の観察を超える値は、モデルから計算した推定値 / 修正例は「18日から254日（84日を超える値は曲線から推定したもの）」 / https://emotionalfirstaidacademy.com/wp-content/uploads/2023/10/How-habits-are-formed.pdf
- 運動は飲食より「自動性が高まりにくい」と書く場合 / 自動性の到達水準（漸近線）は飲食34・飲料35・運動35で差はない（p=.708）。違いの記述があるのは到達日数（65・59・91日）だけで、これも有意ではない（p=.328）。論文自身、検出力が足りず結論は出せないとしている（p.1007） / 修正例は「運動は頭打ちに達するまで約1.5倍長くかかる傾向があったが、有意差はなかった」 / https://emotionalfirstaidacademy.com/wp-content/uploads/2023/10/How-habits-are-formed.pdf
