---
title: "DB統合テストの3ボトルネックと解消戦略（Go + PostgreSQL）"
sources:
  - "https://techblog.enechain.com/entry/fast-robust-go-db-tests"
created: "2026-05-20"
updated: "2026-05-23"
---

# DB統合テストの3ボトルネックと解消戦略（Go + PostgreSQL）

## 概要

DB統合テストのコストは「マイグレーション時間×テスト数」「環境差異による起動失敗」「プロセス起動の繰り返し」という3つの独立したボトルネックから構成される。それぞれを独立した戦略で解消することで、テスト1件あたりの初期化コストをユニットテストに近いレベルまで下げられる。Go+PostgreSQLでは `GetDatabase(t)` の1行APIを実現でき、1パッケージあたりの初期化コストを約8秒から250ms以下に削減できる。

```go
func TestSomething(t *testing.T) {
    db := pi.GetDatabase(t) // マイグレーション済みの空DBを取得
    // t.Cleanup()でテスト終了時にDBが自動削除される
}
```

## 3ボトルネックと解消戦略

### ボトルネック1: マイグレーション時間×テスト数
**解消戦略: 初期化状態の1回作成と複製**

マイグレーションを1回だけ実行して「初期化済みDB状態」を保存し、各テストにはそのスナップショットを複製して渡す。複製コストはマイグレーション実行コストと独立しているため、テスト数が増えても合計マイグレーション時間は一定に保たれる。

PostgreSQLの `CREATE DATABASE ... TEMPLATE` 構文でマイグレーション済みDBをファイルレベルコピーする（[[postgresql-template-database]] 参照）。ランダム名のDBを使うことで `t.Parallel()` による並列実行でもデータ汚染が起きない。

### ボトルネック2: 環境差異による起動失敗
**解消戦略: 環境自動検出と起動方法の抽象化**

ローカル・CI・コンテナなど環境ごとに異なる起動コマンドは、コマンドの存在確認と環境変数で判定し、適切な起動方法を自動選択することで吸収する。呼び出し側は環境の違いを意識せず単一のAPIで使える。

| 環境 | 判定条件 | 起動方法 |
|------|---------|---------|
| macOS | `pg_ctl` が存在 | `pg_ctl init` + `pg_ctl start`（ランダムポート） |
| Debian/GitHub Actions | `pg_createcluster` が存在かつ `RUNNER_ENVIRONMENT=github-hosted` | `sudo pg_createcluster` |
| Docker専用 | 上記コマンドが不在 | Testcontainers |

```go
var checkInstallPostgresLocally sync.Once
checkInstallPostgresLocally.Do(func() {
    if _, err := exec.LookPath("pg_ctl"); err == nil {
        canUseLocalPostgres = true
    }
    if _, err := exec.LookPath("pg_createcluster"); err == nil {
        canUseLocalPostgres = true
        runningOnDebian = true
    }
})
```

起動完了の検出: プロセスベースでは `sql.Open()` → `Ping()` を100ms間隔でポーリング。Testcontainersでは `wait.ForExposedPort()` とログパターンマッチングを使用。

### ボトルネック3: プロセス起動の繰り返し
**解消戦略: プロセス共有と接続情報の受け渡し**

DBプロセスをテストスイート（またはCIジョブ）の開始時に1回だけ起動し、接続情報をファイルや環境変数で後続プロセスに渡す。テストパッケージをまたいでプロセスを共有することで、起動コストをテスト全体に分散できる。

GitHub ActionsのstepをまたいでPostgreSQLを再利用するため、接続情報をJSON形式で `$GITHUB_ENV` に書き出す。

```yaml
steps:
  - run: go run ./cmd/test-postgresql >> $GITHUB_ENV
  - name: Run unit tests
    run: go test ./...
```

### ゾンビプロセス対策

`t.Parallel()` 並列実行中にpanicが起きると `TestMain` のdeferが呼ばれずPostgreSQLプロセスが残留する。Goのバグ（[golang/go#49929](https://github.com/golang/go/issues/49929)）により `t.Failed()` がpanic時にfalseを返すため、reflectで `testing.common.finished` フィールドを直接参照してpanicを検出する。

```go
func testFailed(t testingT) bool {
    if t.Failed() {
        return true
    }
    v := reflect.ValueOf(t).Elem()
    finished := v.FieldByName("common").FieldByName("finished").Bool()
    return !finished
}
```

Goの内部実装に依存するため将来のバージョンアップで破損するリスクがある。GitHub Actionsではランナーがジョブ終了時に破棄されるためゾンビ対策は不要。

## 効果

| パッケージ | 改善前 | 改善後 | オーバーヘッド |
|-----------|-------|-------|--------------|
| internal/A | 8秒 | 247ms | 約3% |
| internal/B | 8秒 | 353ms | 約4% |
| internal/C | 7秒 | 246ms | 約3.5% |

## 関連

- [[postgresql-template-database]] — ボトルネック1の解消に使うPostgreSQLのテンプレートDB複製機能
- [[test-reliability-design]] — DB統合テストはミディアムに分類されるが、このパターンでスモールに近いコストを実現する。テストサイズ分類の定義を含む
