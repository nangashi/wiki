---
title: "Claude Code組織セキュリティ設定（managed-settings + MDM）"
type: "リファレンス型"
sources:
  - "https://note.com/kajinari/n/n6494b35a4826"
created: "2026-05-23"
updated: "2026-07-02"
---

# Claude Code組織セキュリティ設定（managed-settings + MDM）

## 概要

Claude Codeを組織で安全に展開するには「認証・ガードレール・コスト可視化・段階的展開」の4層が必要。中核はMDM（Jamf等）経由で配布する `managed-settings.json` によるガードレールと、1Password CLIによるAPIキーの平文保存禁止。

## 詳細

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

## 関連
- [[indirect-prompt-injection]] — managed-settingsで防御するIPI攻撃の仕組み
