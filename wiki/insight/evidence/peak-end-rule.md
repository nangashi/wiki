# 外部検証記録: peak-end-rule

独立評価者による外部検証を検証ごとに追記する。過去の節は書き換えない。

## 2026-09-25T13:54:31Z run=781e4ea9a92e

- target: wiki/insight/designs/peak-end-rule.md
- target_blob: 48324f29f5cb6ee2e0bf86d79d42c4e5cc243a2e
- evaluator: claude / opus

### 確認済み

- A1 参加者は男子大学生32人 / Kahneman et al. 1993, p.402 Method「Subjects」: "Thirty-two male University of California students, age 19 to 39 (median age = 22.5)"。データ不備などで入れ替えた3人を含む / https://www.ius.uzh.ch/dam/jcr:9ac245ec-ce2c-46a6-a620-77bf34f05d61/Kahneman%20et%20al.%20When%20More%20Pain%20is%20Preferred%20to%20Less.pdf
- A2 32人中22人（69%）が長い試行を再体験に選んだ / 同 p.403 Results: "most subjects (22 of 32, or 69%) preferred to repeat the long trial (z = 2.15, p < .05 by sign test)"。長い試行は14℃で60秒のあと、さらに30秒浸けたまま水温を少し上げる（p.401 Abstractでは約15℃、p.403では平均14.1℃から15.2℃）ので「約15℃」の記述と合う / 同上URL
- A3 終わりの30秒で不快感が下がったかどうかで選好が分かれた / 同 p.403: "Among the 21 subjects who showed a decrement of 2 or more points, 17 (or 81%) preferred the long trial; the 11 subjects who showed little or no decrement of discomfort split 6:5 in favor of the short trial"。「下がった」の基準は2点以上の低下、「下がらなかった」11人は1点以下の低下（2人は上昇）だった。記事で数値を示すならこの基準も添えるとよい / 同上URL
- A4 持続時間が判断に効きうる条件 / 同 p.404 General Discussion: "duration could play a role in the evaluation of affective episodes that are either very much longer or very much shorter than expected." 同じ段落では、改善・悪化する傾向の速さ（Hsee & Abelson 1991）が評価に効くこと、始まりに支配される場合、終わりだけが効く場合にも触れている / 同上URL
- B1 参加者682人。介入は処置の終わりに短い区間を追加し、その間スコープの先端を直腸に留めた / Redelmeier, Katz & Kahneman 2003 Abstract（733人に声をかけ682人が同意、標準345・修正337はTable 1）。2.3節: "the tip of the colonoscope was allowed to rest in the rectum for up to 3 min prior to removal (no suction, inflation, or added anaesthetic)"。終盤の痛みは1.7 vs 2.5（P<0.001、Table 3）、全体の時間は修正群が約1分長い（27.6 vs 26.8分） / https://yorkspace.library.yorku.ca/bitstreams/6a4a5d51-28ba-486b-88c9-00d873833b09/download
- B2 事後の痛み評価は4.4 vs 4.9で、約10%低い / 同 Abstract と Table 4: VAS 4.4±2.5 vs 4.9±2.6（P=0.006）。3.3節: "a 10% lower mean rating on the visual analogue scale"。順位評価は4.1 vs 4.6（P=0.002） / 同上URL
- B3 再受診率は調整なしで53% vs 48%（P>0.20）、調整後はOR 1.41（P=0.038） / 同 3.4節: "no large general effect on increasing subsequent return rates (53 vs. 48%, P > 0.20)"。調整なしの推定は18%増（95%CI −13〜59）。既往・適応・異常所見で調整すると "41% increase in the odds of returning (95% confidence interval: 2–96, P = 0.038)"（Abstract: odds ratio = 1.41）。追跡期間の中央値は5.3年 / 同上URL
- C1 時間に注意が向く（目立つ）と持続時間の寄与が大きくなる / Ariely, Kahneman & Loewenstein 2000 Joint Comment, JEP:Gen 129(4), pp.524–525: "people ... will rely on this variable when it is made sufficiently salient"、"none of us expects to observe complete duration neglect when attention is explicitly or implicitly drawn to this variable"。被験者内操作で持続時間の効果が出ることも認めている。Ariely & Loewenstein 2000（pp.508–523）Abstract: "response modes that reduce reliance on conversational norms or standard of comparison also increase the attention that participants pay to duration" / https://web.mit.edu/ariely/www/MIT/Papers/duration1c.pdf ; https://scholars.duke.edu/individual/pub810373
- C2 時間と強度が結びつく（強度が時間とともに変わる、傾きが効く）場合 / Ariely 1998, JBDM 11(1):19–45 Abstract（Duke Scholars掲載）: 回顧評価を主に決めるのは "a combination of the final pain intensity and the intensity trend during the latter half of the experience"。持続時間は強度がほぼ一定の刺激ではほとんど効かず、強度が時間とともに変わると効く。Joint Comment p.524も、想起される特徴として "peak (or trough), ending value, and slope" を挙げている / https://scholars.duke.edu/publication/861419
- C3 長期・複合体験ではピーク・エンドの説明力が弱まり、平均などの別指標が効く（研究単位での支持） / Kemp, Burt & Furneaux 2008, Memory & Cognition 36:132–138（PMID 18323069）Abstract: 学生49人・平均7日の休暇で "The duration of the vacation had no effect"、"A number of summary measures provided reasonable prediction"、"The peak-end rule was not an outstandingly good predictor"。Strijbosch et al. 2019, Front Psychol 10:1705: 複雑で異質な体験では "peak and end emotional valence are inferior to other measures (such as averaged valence and arousal ratings...)" / https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22peak-end%20rule%20with%20extended%20autobiographical%20events%22&resultType=core&format=json ; https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.01705/full

### 未確認

- C3のうち「反復するセッションの総体」でピーク・エンドが弱まるという部分 / 反復セッションを直接扱う一次資料は取得できなかった。Kemp 2008は1回の休暇（数日）、Strijbosch 2019はVR映像の体験である。Ariely & Zauberman 2000（体験の分割・結合）と Schreiber & Kahneman 2000 は本文も抄録も取得していない / 反復セッションに触れるなら、Ariely & Zauberman 2000 の本文で確かめてから引用する。確かめられなければ「数日規模の単発の長期体験」に限定して書く
- C3を一般則として述べてよいか / Alaybek et al. 2022（OBHDP 170, 104149、174効果量）は二次情報（EconPapers・CoLab）でしか確認していない。そこでは、ピーク・エンド効果は r=0.581 と大きく、検討した調整要因をまたいで頑健とされ、全体平均と同程度の予測力で、持続時間の効果は "essentially nil" とされる。体験の長さを調整要因として調べた結果はあるのか、あるならどの向きかは、本文を取得できず確認できていない（ScienceDirectは403） / Alaybek 2022 本文の調整要因分析を確認する。記事では「個別研究（Kemp 2008、Strijbosch 2019）では弱まったが、メタ分析は全体として頑健性を報告している」と両方を示すのが安全
- Ariely & Loewenstein 2000 本論文の本文（どの実験条件で持続時間の効果が出たか） / Abstractと Joint Comment しか確認していない / 具体的な実験条件を書くなら本文 pp.508–523 で確かめる

### 誤り

- なし
