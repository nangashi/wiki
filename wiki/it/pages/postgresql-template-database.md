---
title: "PostgreSQLテンプレートDB（CREATE DATABASE TEMPLATE）"
type: "リファレンス型"
sources:
  - "https://techblog.enechain.com/entry/fast-robust-go-db-tests"
created: "2026-05-22"
updated: "2026-05-23"
---

# PostgreSQLテンプレートDB（CREATE DATABASE TEMPLATE）

## 概要

PostgreSQLの `CREATE DATABASE ... TEMPLATE` 構文を使ったテスト用DB高速作成パターン。マイグレーション済みDBをテンプレートとして保持し、テストごとにファイルレベルコピーで新DBを取得することで、マイグレーション実行コストをスイート全体で1回に抑えられる。毎回マイグレーションを実行する方式と比べてテスト初期化が大幅に速く、トランザクションロールバック方式と違いトランザクション内部の動作もテストできる。

## 他のDB分離方式との比較

| | テンプレートDB | トランザクションロールバック | 毎回マイグレーション実行 |
|---|---|---|---|
| 主な用途 | 並列統合テスト | 単純なCRUDテスト | 確実な初期化が必要なテスト |
| マイグレーション実行回数 | スイートで1回 | スイートで1回 | テストごと |
| 並列テスト対応 | ○ | △（分離に注意が必要） | ○ |
| トランザクション内動作のテスト | ○ | ✗ | ○ |
| PostgreSQL依存 | ○（PostgreSQL固有機能） | ✗ | ✗ |

## 採用すべきケース

- **テスト数が多くマイグレーション時間がボトルネックになっている**: テストごとのマイグレーション実行コストを排除できる
- **並列テストが必要**: テストごとに独立したDBを持つため `t.Parallel()` と相性がよい
- **トランザクションを伴う処理のテスト**: コミットを含む実際のDB操作を検証する必要がある場合

## 採用しないべきケース

- **テスト数が少なくマイグレーション時間が問題にならない**: テンプレートDB管理の実装コストが見合わない
- **PostgreSQL以外のDB**: この機能はPostgreSQL固有。MySQL・SQLiteには同等の仕組みがない
- **各テストがトランザクション内で完結できる単純なCRUD**: ロールバック方式の方がシンプルで十分

## 実装のアンチパターン

### 1. テンプレートDBへの直接接続

テンプレートDBにセッションが残った状態で `CREATE DATABASE ... TEMPLATE` を実行するとエラーになる。

```sql
-- Bad: テンプレートDBに直接接続してクエリを実行
\c template_db
SELECT * FROM users;  -- セッションが残るとCREATE DATABASE が失敗する

-- Good: テンプレートDBへの直接接続は禁止し、コピー先DBのみ使う
CREATE DATABASE test_abc123 TEMPLATE template_db;
\c test_abc123
```

### 2. テスト間でDB名を固定する

テスト名や連番をDB名に使うと並列実行時に競合する。

```go
// Bad: 固定のDB名で並列テストが競合する
dbName := "test_db"
createDB(dbName)

// Good: ランダムなサフィックスで並列テストの干渉を防ぐ
dbName := fmt.Sprintf("test_%s", uuid.New().String()[:8])
createDB(dbName)
```

### 3. マイグレーション変更後にテンプレートを再作成しない

テンプレートDB作成後のマイグレーション変更はコピー済みDBに反映されない。

```go
// Bad: テンプレートDBを使い回す（古いスキーマのまま）
func setupTemplate() {
    if templateExists("template_db") {
        return  // 古いテンプレートをそのまま使う
    }
    createTemplate("template_db")
}

// Good: マイグレーションファイルのハッシュでテンプレートの鮮度を検証する
func setupTemplate() {
    currentHash := hashMigrationFiles()
    if templateExists("template_db") && templateHash() == currentHash {
        return
    }
    dropAndRecreateTemplate("template_db")
}
```

## 実装でトレードオフが生じるケース

### テンプレートDB再作成のタイミング

| アプローチ | メリット | デメリット |
|-----------|---------|-----------|
| マイグレーションファイルのハッシュで検知 | 変更時のみ再作成でムダがない | ハッシュ計算・比較ロジックが必要 |
| テストスイート起動時に常に再作成 | シンプルで確実 | スイート起動のたびにマイグレーション実行コストが発生 |

**推奨**: マイグレーションファイル数が少ない初期はスイート起動時に常に再作成。ファイルが増えて起動コストが気になりだしたらハッシュ検知に切り替える。

### 並列テスト数とDB接続数

並列テスト数が増えると同時接続数が増大しPostgreSQLの `max_connections` を圧迫する。

対策の選択肢:
- **接続プールの上限設定**: テストごとのDB接続数を制限する（例: `SetMaxOpenConns(2)`）
- **テスト並列度の制限**: `t.Parallel()` を使うテスト数に上限を設ける
- **PostgreSQLの設定調整**: `max_connections` を引き上げる（テスト環境のみ）

## 関連

- [[db-integration-test-bottlenecks]] — DB統合テストのボトルネック全体像と解消戦略。このパターンのGoでの実装例を含む
