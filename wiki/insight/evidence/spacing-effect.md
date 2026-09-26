# 外部検証記録: spacing-effect

独立評価者による外部検証を検証ごとに追記する。過去の節は書き換えない。

## 2026-09-26T00:24:01Z run=63d0d59c5006

- target: wiki/insight/designs/spacing-effect.md
- target_blob: 3d58150ed23b9d38274d50d24cfe0e18a72624f9
- evaluator: claude / opus

### 確認済み

- A1 書誌: Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. Psychological Bulletin, 132(3), 354–380. doi:10.1037/0033-2909.132.3.354 / Crossrefのメタデータ（巻132・号3・頁354–380）。2008年論文の文献欄にも「132, 354-380」とある / https://api.crossref.org/works/10.1037/0033-2909.132.3.354
- A2 学習時間をそろえた条件で、分散は集中より後日の再生が良い / 2006年論文のin press原稿（eScholarship版）p.6–7 "Spacing Effects: Massing vs. Spacing"。集中と分散の比較は271件、効果量は23件。"Only 12 of 271 comparisons ... showed no effect or a negative effect from spacing"。p.7に "the amounts of study time for massed and spaced items were equivalent"。要約（p.14）に "spaced (vs. massed) learning of items consistently shows benefits, regardless of retention interval"。ページ番号は原稿のもので、雑誌の頁との対応は取れていない / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- A3 保持間隔（RI）が長くなるほど最適な学習間隔（ISI）も長くなる、という結論 / 抄録に "the ISI producing maximal retention increased as retention interval increased"。p.10に「RIが1分未満ならISIも1分未満が最適、RIが6か月以上ならISIは少なくとも1か月が最適」とある / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- A3 根拠の範囲 / 対象は言語記憶課題の再生テストだけ（p.4。対連合・手がかり再生、リスト、事実、文章、綴り、顔の名前など。再認や頻度判断は除外）。427本を検討し、条件を満たしたのは184本の論文にある317実験（正答率の値958件、分散学習の評価839件、効果量169件）。正答率の差のうち80%はRIが1日未満で、1か月を超えるのは4%だけ（p.7）。RIとISIがともに1日以上で交絡のない研究は、5本の論文にある7実験（p.9）。参加者の85%は若年成人（p.14） / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- A4 間隔が長すぎる場合の記述 / p.10に「RIに対してISIが長い場合、ISIをさらに延ばすと正答率が下がる（最適ISIをもつ非単調な関係）」とある。一方、p.13–14では、最適より長いISIでどれだけ成績が落ちるか（"magnitude of the drop-off produced by use of a supra-optimal ISI"）は未解決の問いとされている / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- B 書誌: Cepeda, Vul, Rohrer, Wixted & Pashler (2008), Psychological Science, 19(11), 1095–1102, doi:10.1111/j.1467-9280.2008.02209.x / Crossrefのメタデータ / https://api.crossref.org/works?query.bibliographic=Spacing+effects+in+learning+temporal+ridgeline+optimal+retention&rows=2
- B1 参加者・材料・ISIとRIの範囲 / in press原稿（ERIC ED505660）p.3–4、表1。インターネット上の参加者1354人を26条件に無作為に割り付けた。平均34歳、女性72%。材料は、あまり知られていない事実を問う雑学問題32問（答えは5〜6文字の1語）。ISIは0〜105日（0, 1, 2, 4, 7, 11, 14, 21, 35, 70, 105日）、RIは7, 35, 70, 350日。最終テストは再生と5択再認。抄録には "over 1350 individuals"、ISIは "up to 3.5 months"、RIは "up to 1 year" とある。ページ番号は原稿のもの / https://files.eric.ed.gov/fulltext/ED505660.pdf
- B2 最適な間隔のRIに対する比率は、RIが長くなるほど下がる / 抄録に "The optimum gap value was about 20% of the test delay for delays of a few weeks, falling to about 5% when delay was one year"。p.4では、テストした間隔のうち再生で最適だったのはRI 7/35/70/350日に対してそれぞれ1/11/21/21日（再認では1/7/7/21日）。p.5では、当てはめた関数での最適はRI 350日に対して23日（7%）。図4の説明に "a decrease in the ratio of optimal gap to test delay" / https://files.eric.ed.gov/fulltext/ED505660.pdf
- B3 最適より短すぎる間隔の損失は、長すぎる間隔の損失より大きい / p.6に "while there are costs to using a gap that is longer than the optimal value, these costs are much smaller than the costs of using too small a gap"。理由として、間隔を延ばすと正答率は急に上がり、その後はゆっくり下がることを図3で示している / https://files.eric.ed.gov/fulltext/ED505660.pdf
- C1 書誌: Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), Psychological Science in the Public Interest, 14(1), 4–58, doi:10.1177/1529100612453266 / Crossrefのメタデータ / https://api.crossref.org/works/10.1177/1529100612453266
- C2 分散学習の評価は high utility / 9.5 "Distributed practice: Overall assessment"（pp.39–40）に "we rate distributed practice as having high utility: It works across students of different ages, with a wide variety of materials, on the majority of standard laboratory measures, and over long delays. It is easy to implement (although it may require some training) and has been used successfully in a number of classroom studies" / https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf
- C2 一般性の範囲 / 9.2b（p.37）: 就学前児から高齢者、臨床群まで効果がある。9.2c（pp.37–38）: 定義、顔と名前の組、外国語の語彙、雑学、文章、講義、絵のほか、数学・歴史・音楽・外科の技能にも効果がある。9.2d（p.38）: 再生以外の測度にも一般化しており、数か月から数年の遅延でも効果がある / https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf
- C2 限界 / p.38: 飛行機操縦のような複雑な課題では効果が小さいか、ない場合もある（Donovan & Radosevich, 1999）。IESガイドの "few studies have examined acquisition of complex bodies of structured information" を引用。再生以外の教育的な測度への一般化が最大の穴、とも書く。p.39（9.4）: 教科書の構成、試験直前に学習が集中する傾向（procrastination scallop）、学習者が利点を理解していない可能性、という導入上の障害。p.40: 複雑な材料、個人差、高次の認知課題、分散した学習と分散した想起の切り分けが今後の課題 / https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf
- D1 Ebbinghausが自分を被験者にし、無意味綴りを使い、再学習で節約された労力の割合で保持を測った / Ruger & Bussenius訳（1913）の第3章 §11（無意味綴りの作り方）、§14（"The subject, as I myself always did"）。第7章 §27–28 では、節約された労力を最初の学習時間に対する百分率Qで表している。§29前後の結果は、約20分で58%、1時間で44%、9時間で36%、1日で34%、2日で28%、6日で25%、31日で21%（1879–80年、163組の二重テスト） / https://psychclassics.yorku.ca/Ebbinghaus/memory7.htm
- D2 68回と38回の観察 / 第8章 "Retention as a Function of Repeated Learning" の §34 に "38 repetitions, distributed in a certain way over the three preceding days, had just as favorable an effect as 68 repetitions made on the day just previous"。12音節の系列で、同じ再学習効果に必要な回数を比べたもの / https://psychclassics.yorku.ca/Ebbinghaus/memory8.htm
- E1 Kornell & Bjork (2008), Psychological Science 19(6), 585–592 / 画家12人の絵を6枚ずつ学習させ、画家ごとにまとめて見せる（集中）か他の画家の絵と交互に見せる（分散）かを比べた。実験1aは120人、1bは72人、実験2は80人。どの実験でも分散の方がテスト成績が良かった。実験1aではテストの後でも、78%の参加者が分散の方が成績が良かったのに、78%が集中を分散と同等以上と答えた（p.588）。実験1aと2を合わせると、85%が分散で同等以上の成績だったのに、83%が集中を同等以上に効果的と評価した（p.591）。抄録に "Participants rated massing as more effective than spacing, even after their own test performance had demonstrated the opposite" / https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/07/Kornell_Bjork_2008_PsychScience.pdf
- E1 Kornell (2009), Applied Cognitive Psychology 23(9), 1297–1317, doi:10.1002/acp.1537 / GREの語彙をウェブ上のフラッシュカードで学ぶ実験。大きな束1つで学ぶ（分散）方が小さな束4つで学ぶ（集中）より効果的で、詰め込みより効果的でもあった。実験全体で、90%の参加者にとって分散の方が効果的だったが、72%は集中の方が効果的だったと考えた。本文ではなく、Crossref経由で取得した抄録の要約だけで確認した / https://api.crossref.org/works/10.1002/acp.1537
- E1 補足 / Dunlosky et al. (2013) p.39もKornell & Bjork (2008) を引用し、学習者は分散の利点を経験した後でも集中の方をよく学べたと評価する、と述べている / https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf
- E2 直後テストでは集中が有利になることがある / Dunlosky et al. (2013) p.38 に "the distributed-practice effect is often stronger on delayed tests than immediate ones, with massed practice (cramming) actually benefitting performance on immediate tests (e.g., Rawson & Kintsch, 2005)"。同p.35 にも "cramming is better than not studying at all in the short term" / https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf
- E2 反対側の記述（併記が必要） / Cepeda et al. (2006) p.6–7 は、集中が有利になるのはRIが2〜4秒といった極端に短い場合だけ（"Peterson Paradox"）とし、RIが1分未満でも分散は9%上回ったと報告する。さらに "there is no hint that massed presentation is preferable to spaced, whether retention interval is very short (less than one min) or very long" とある / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- F1 機序には複数の説明があり、決着していない / Cepeda et al. (2006) p.11–13 "Implications for Theories": "Many theories purport to account for distributed practice effects, and little consensus has been achieved"。検討したのは、処理不足説（deficient processing）、符号化変動説（encoding variability）、固定化説（consolidation）、学習段階想起説（study-phase retrieval）の4つ。処理不足説は "does not readily survive" とされ、残りの3つは候補として残る / https://www.escholarship.org/content/qt3rr6q10c/qt3rr6q10c.pdf
- F1 同じ趣旨の記述 / Dunlosky et al. (2013) p.36 は、処理不足、想起の手がかり（reminding）、固定化を挙げ、"accounts currently under debate" "multiple mechanisms may contribute" と書く。Cepeda et al. (2008) p.5–6 は、処理不足説と全か無か説はデータに合わず、符号化変動説と学習段階想起説は合致しうる、と書く / https://files.eric.ed.gov/fulltext/ED505660.pdf

### 未確認

- A1–A4 と B の頁 / 読んだのは著者のin press原稿（eScholarship版とERIC版）だけで、雑誌の頁（354–380、1095–1102）との対応は取れていない。Dunlosky (2013) は、2006年論文で「RIが1か月を超える研究はすべて分散に利点があった」とする一文の出典を p.370 としている / 記事で頁を示すなら、出版版で確認するか、節名で示す
- 2006年論文の研究数を「254研究・14,000人超、分散47%対集中37%」とする記述 / これは Dunlosky et al. (2013) p.36 による要約。2006年論文の抄録と本文は「184論文・317実験・839評価」で、読んだ範囲に254や47%対37%は見つからなかった / 記事に書くなら Dunlosky (2013) の要約として出典を示すか、2006年論文の数値を使う
- Kornell (2009) の詳細（各実験の人数、72%がいつ判断した値か、学習中の成績は集中の方が良く見えたか） / 本文PDF（Williamsサイト、Wiley）は403で取得できず、Crossref経由の抄録要約しか読めていない / 本文を入手して実験ごとの値を確かめる
- E1のうち「分散すると直後の成績が集中より悪く見える」 / Kornell & Bjork (2008) では、テストのどのブロックでも分散の方が成績が良かった。学習中の成績についての記述は読んだ範囲になかった。流暢さのために集中の方がよく学べたと感じる、という説明はある（p.586, p.590） / 学習中の成績の差を根拠にするなら別の資料（例: Kornell 2009の本文）で確かめる
- D1の「一人だけが被験者」 / 自分が被験者であることは §14 の "as I myself always did" と §30 の "only for my own case" から読み取れる。一方、「唯一の被験者」と明言した文は、読んだ章（3・4・7章）では見つからなかった / 序文や第1〜2章を確かめるか、「自分を被験者として」という表現にとどめる
- 原典の独語版（archive.org b28111710） / 取得していない / 必要なら §34 の独語原文と頁を確かめる

### 誤り

- B2の例示「RI 1週間で最適な間隔は20〜40%、1年で5〜10%程度」 / Cepeda et al. (2008) の抄録は「数週間の遅延で約20%、1年で約5%」。RI 7日で再生の成績が最も良かった間隔は1日（約14%）で、2日（約29%）ではなかった（p.4）。当てはめた関数での最適はRI 350日に対して7%（p.5）。「1週間で20〜40%」は論文に出てこない。Dunlosky (2013) p.37 の要約は「おおむねRIの10〜20%。1週間なら12〜24時間、5年なら6〜12か月」 / 抄録どおり「最適な間隔は、数週間先のテストでは遅延の約20%、1年先では約5%（関数の当てはめでは7%）に下がる」と書く / https://files.eric.ed.gov/fulltext/ED505660.pdf
