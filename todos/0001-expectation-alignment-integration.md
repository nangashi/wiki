# 期待値調整の記事統合

## 方針

期待値調整は独立した原理ではなく、参照点依存性を踏まえた応用として扱う。期待が参照点になる説明と期待値調整の応用をプロスペクト理論へ、用途・成果物・品質・期限の確認を貢献への集中へ統合する。「満足の形成」の独立記事は作らない。

統合後は期待値調整の記事・designを削除する。検索入口はプロスペクト理論の本文に「期待値調整」を含めて確保し、案内記事は残さない。

## 完了したこと

- [x] insightの既存記事を検索し、プロスペクト理論との原理の重なり、貢献への集中との用途適合の重なりを確認した。潜在的可能性の台地は関連する適用場面、アンカリング・フレーミングは別概念として整理した。
- [x] 出典を確認した。Kahneman & Tversky (1979) p.274は期待が参照点に影響することを支持する。Rutledge et al. (2014) とSchieblerらのメタ分析は補助根拠と限界に用い、満足全般をプロスペクト理論から導かない。大石哲之の書籍抜粋は業務上の確認方法を支持する。URL・支持範囲は統合先designに記録済み。
- [x] [プロスペクト理論のdesign](../wiki/insight/designs/prospect-theory.md)を更新した。D4・D5に期待を参照点として捉える理解と期待値調整の応用を追加した。
- [x] [貢献への集中のdesign](../wiki/insight/designs/focus-on-contribution.md)を更新した。D3の具体例として依頼内容の確認を統合し、出典S7を追加した。
- [x] `wiki/insight/designs/expectation-alignment.md`を一時的な統合設計へ変更した。恒久的に残す設計ではなく、統合完了後の削除対象とする。
- [x] 3件のdesignをfreshな独立evaluatorでレビューし、すべて必須修正なしで保存した。評価保存時の形式・hash検証と`git diff --check`を完了した。

設計評価の記録:

- [prospect-theory](../evaluations/insight/prospect-theory/design/20260913T130619Z-v1-5fda43640415.md)
- [focus-on-contribution](../evaluations/insight/focus-on-contribution/design/20260913T130659Z-v1-0ce0dbaecf50.md)
- [expectation-alignment（統合設計）](../evaluations/insight/expectation-alignment/design/20260913T130619Z-v1-5e82f2745d8d.md)

記事本文・被リンク・indexは未変更。designの合格は本文の完成・公開条件の充足を意味しない。評価履歴は旧記事の削除後も履歴として保持する。

## これからやること

1. [ ] **変更済みdesignに沿ってGeminiが本文を執筆する。** 対象は`wiki/insight/pages/prospect-theory.md`と`wiki/insight/pages/focus-on-contribution.md`の2件。統合先design、根拠資料、記事schema、品質・日本語基準を渡す。期待値調整の独立記事は再執筆しない。
2. [ ] 執筆した2記事で、原理と応用、比較基準の違いと用途不適合、研究の実証範囲と実務提案を混同していないか確認する。出典・関連リンク・updatedを確定する。
3. [ ] 被リンクを再取得し、文脈に応じて統合先へ変更する。前回の取得では`wiki/insight/pages/fact-interpretation-action.md`から参照があった。変更した関連先も検査・評価対象に含める。
4. [ ] **統合内容が本文に反映された後、旧記事と旧designを削除する。** 対象は`wiki/insight/pages/expectation-alignment.md`と`wiki/insight/designs/expectation-alignment.md`。案内記事は残さない。
5. [ ] 対象wikiの手順に従い、変更記事のtextlint・出典・構造検査と、独立した記事単独読解→設計照合の評価を実施・保存する。必須修正があれば改善・再評価する。Geminiによる執筆と独立評価を分離する。
6. [ ] 公開・終了条件を確認後、`python3 tools/wiki/wiki_structure.py index --collection insight`でindexを更新する。旧slugへの参照切れ、indexと概要の一致、記事・design・評価のhash整合を確認する。旧indexには期待との差分だけで評価を説明する古いサマリが残っているため、更新漏れに注意する。

執筆・評価の入口は[設計手順](../wiki/insight/workflows/design.md)と[評価プロトコル](../wiki/insight/references/evaluation-protocol.md)。このTODOは引き継ぎ用であり、wiki固有の検査・評価・公開手順を置き換えない。
