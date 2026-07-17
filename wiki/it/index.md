# IT Wiki インデックス

全IT wikiページの目次。`/ingest` 実行時に自動更新される。

エントリ形式: `- [[slug]] — 1〜2文のサマリ`

---

- [[postgresql-template-database]] — PostgreSQLテンプレートDBリファレンス。マイグレーション1回+ファイルコピーで並列統合テストを高速化。アンチパターン・他のDB分離方式との比較・Go実装事例（初期化コスト8秒→250ms以下、環境自動検出・プロセス共有含む）を収録
- [[wide-events-implementation]] — Wide Eventsリファレンス。採用判断・3つの実装アンチパターン・ストレージ選定（ClickHouse/BigQuery）・テイルサンプリング戦略のトレードオフ
- [[test-reliability-design]] — テスト信頼性設計の3層：テストの2種類の嘘（偽陽性/偽陰性）・テストサイズによる構造的防止・フレイキーCIパイプライン分離管理
- [[test-design]] — テストケース設計：禁止トレース・フェイルのサンプリングとして検証を捉え、計画主導テストと探索的テストで網羅する
- [[claude-code-managed-settings]] — Claude Codeの組織セキュリティ設定。設定5層の優先順位・managed-settings.json+MDM（Jamf）配布・1Password CLI連携・段階的展開（Lv0〜Lv4）・制限強度と生産性のトレードオフ
- [[ai-coding-eslint-constraints]] — AIコーディング品質を担保するESLint制約設計。eslint-plugin-boundariesによる依存方向強制・禁止ルール・結合テスト戦略・採用判断（クラスベースFWとの非互換等）とトレードオフ
- [[adr]] — Architecture Decision Recordの構造と活用。コンテキスト・決定・結果の3要素で技術選定の前提を記録し、撤退判断を記録に基づいて行う。採用判断基準と4つのアンチパターン（おとぎ話・メガADR・ゾンビADR・書いたら終わり）を含む
- [[jwt]] — JWT（JSON Web Token）リファレンス。採用判断・非採用ケース・7つの実装アンチパターン（Bad/Good例付き）・失効問題/HS256 vs RS256/レースコンディションのトレードオフを網羅
- [[ai-context-management]] — LLMの4つの構造的特性（非決定論・コンテキスト絶対化・恣意的解釈・知識-活用乖離）と、指示の4層構造・観点先行条件を含むコンテキスト設計の実践パターン
- [[ai-agent-design]] — AIエージェントは業務列挙でなく役割から設計する。役割先行設計・1エージェント1役割の原則に加え、マルチエージェント化の採用判断（読み込み中心は向く・書き込み中心は不向き・トークン約15倍）を含む
- [[indirect-prompt-injection]] — 外部テキストに悪意ある指示を埋め込みエージェントに実行させる攻撃手法。5層の多層防御比較・アンチパターン・実事例（Clinejection・HashJack等）・セキュリティvsユーティリティのトレードオフ
- [[llm-knowledge-system]] — LLM知識システムパターン（Karpathy）。三層アーキテクチャ・Ingest/Query/Lint操作・RAGとの比較（書き込み時コストと読み出し一貫性の交換）・採用判断を含む実装リファレンス
- [[middle-notation-pattern]] — 中間記法パターン（MNP）。GUIと同等のDSLをAIに操作させる分業設計でAI統合の実装速度・安定性・コスト（4〜8倍削減）を同時改善。Function Calling / Computer Useとの比較と採用判断を含む
- [[saas-authorization-design]] — SaaS権限管理設計（PBAC+ReBAC二層モデル）。「何ができるか」と「誰のリソースか」を分離し、ポリシー集約・スコープ絞り込み・フロントエンド共有を一貫設計するリファレンス
- [[bff-auth-pattern]] — BFFパターンによる認証トークン配置設計リファレンス。ブラウザ境界はCookie・BFF↔API間はJWTという層別設計、NextAuthのトークン露出アンチパターン、「Cookie復権」が退化でない理由を含む
