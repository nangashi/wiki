---
title: "Claude Code組織セキュリティ設定（managed-settings + MDM）"
type: "リファレンス型"
sources:
  - "https://note.com/kajinari/n/n6494b35a4826"
  - "https://code.claude.com/docs/ja/permissions"
created: "2026-05-23"
updated: "2026-07-02"
---

# Claude Code組織セキュリティ設定（managed-settings + MDM）

## 概要

Claude Codeを組織で安全に展開するには「認証・ガードレール・コスト可視化・段階的展開」の4層が必要。中核はMDM（Jamf等）経由で配布する `managed-settings.json` によるガードレールと、1Password CLIによるAPIキーの平文保存禁止。

## 仕組み

### 設定の優先順位

Claude Codeの設定は5層の優先順位を持ち、managed settingsが最上位でユーザー・プロジェクト設定では上書きできない。この一方向の優先構造が「組織ポリシーの強制」を技術的に保証する。

```
managed-settings.json（最優先・上書き不可）
  > CLI引数（--allowedTools 等）
  > .claude/settings.local.json（プロジェクトローカル）
  > .claude/settings.json（プロジェクト共有）
  > ~/.claude/settings.json（ユーザー）
```

権限ルールの評価は deny → ask → allow の順で先勝ちのため、managed settingsのdenyルールはどの層からも許可に反転できない。配置場所はmacOSが `/Library/Application Support/ClaudeCode/`、Linuxが `/etc/claude-code/`。

### 認証層

- ドメインクレームで組織のシャドーテナントを防止
- Okta等のIdPとSSO + MFA必須化
- IdP連携による自動プロビジョニング

### ガードレール層（managed-settings.json）

`managed-settings.json` をMDM（Jamf）経由で全端末に配布する。GitHubで設定を管理し、更新時にGitHub Actions → Jamf APIで自動配布することで設定の陳腐化を防ぐ。

**主な制限項目:**
- `curl` / `bash` を使ったバイナリアップロードの禁止（IPI経由のデータ流出を防止）
- ファイルアクセス範囲の制限
- 実行可能なコマンドのスコープ制限

### APIキー管理（1Password CLI連携）

```bash
# 環境変数に直書きせず、実行時にメモリ上で取得
export ANTHROPIC_API_KEY=$(op read "op://{Vault名}/{アイテム名}/credential")
```

`op://` 形式で1Passwordから実行時に取得し、ディスクに平文が残らないようにする。`~/.env` や `~/.bashrc` への直書き、およびホームディレクトリ配下の平文APIキーファイルは禁止。

### コスト可視化層

Anthropic Console APIを通じて OpenTelemetry + BigQuery で利用量を可視化し、職種・チームごとに使用量を把握・配賦する。

### 段階的展開（Lv0～Lv4）

| レベル | 利用範囲 |
|--------|---------|
| Lv0 | 利用ガイドライン確認のみ |
| Lv1 | Claude.ai（Webのみ） |
| Lv2 | Claude API（制限付き） |
| Lv3 | Claude Code（managed-settings適用） |
| Lv4 | フル権限（承認者のみ） |

理解度テストの定期リマインドと継続学習により、制限を増やすのではなく「安全に回り続ける状態」を維持する。

## 採用すべきケース

- 数十人以上の組織でClaude Codeを標準ツール化する — 個人任せの設定は必ずばらつき、最も緩い端末が攻撃面になる
- 機密データ（顧客情報・認証情報）を扱うリポジトリでエージェントを使う — IPI（[[indirect-prompt-injection]]）経由の流出経路をdenyルールで構造的に塞げる
- MDM（Jamf・Intune等）の配布基盤が既にある — 配布・更新の運用コストが限界的に小さい

## 採用しないべきケース

- 個人開発・数名のチーム — `~/.claude/settings.json` と `.claude/settings.json` の使い分けで足り、MDM配布はオーバーヘッドが利益を上回る
- 配布基盤なしでの手動配布 — 更新が行き渡らず「設定されているはず」という誤った安心感の方が有害。GitHub管理＋自動配布（GitHub Actions → MDM API）が組めるまで待つ

## 実装でトレードオフが生じるケース

- **制限の強度 vs 開発者の生産性**: `curl`/`bash` の広範な禁止はIPI経由の流出を防ぐ一方、正当なデバッグ・検証作業も阻む。全社一律の強い制限か、段階的展開（Lv0〜Lv4）でリスク許容度に応じて権限を分けるかの選択になる。本事例は後者を採用し、制限を増やすのではなく教育と組み合わせて「安全に回り続ける状態」を狙っている
- **中央集権ポリシー vs チーム自律性**: managed settingsは上書き不可のため、チーム固有の正当な例外（特定リポジトリでのDockerビルド等）も一律に塞ぐ。denyを最小限のクリティカル項目に絞り、それ以外はプロジェクト設定層に委ねる設計が現実的

## 関連
- [[indirect-prompt-injection]] — managed-settingsで防御するIPI攻撃の仕組み
