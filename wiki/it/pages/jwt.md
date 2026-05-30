---
title: "JWT（JSON Web Token）"
type: "リファレンス型"
sources:
  - "topic:JWT"
created: "2026-05-23"
updated: "2026-05-23"
---

# JWT（JSON Web Token）

## 概要

JWT（RFC 7519）は認証・認可に使われるトークン形式で、マイクロサービス間通信・M2M・クロスドメインAPIで多く採用される。ヘッダー・ペイロード・署名の3パートをBase64URLエンコードしてドット連結した構造で、署名を検証するだけでトークンの正当性を確認できる。セッションCookieや OAuth opaque token はDBやサーバーサイドの状態管理が必要なのに対し、JWTはサーバーがDBを参照せずに検証できる（ステートレス）のが最大の優位性。デフォルトでは署名のみで暗号化はなく、ペイロードは誰でも読める。

## 他の認証トークンとの比較

| | JWT | セッションCookie | OAuth opaque token |
|---|---|---|---|
| 主な用途 | マイクロサービス認証・M2M | モノリスのセッション管理 | サードパーティAPI認可 |
| ステートレス検証 | ○（DBなし） | ✗（DBでセッション保持） | ✗（認可サーバーに問い合わせ） |
| 即時失効 | ✗（expまで有効） | ○ | ○ |
| クロスドメイン対応 | ○（Bearerヘッダー） | △（SameSite制約あり） | ○ |
| ペイロード参照 | ○（自己完結） | ✗ | ✗ |

## 採用すべきケース

- **マイクロサービス / 分散システムの認証**: 各サービスが公開鍵だけで検証できるため、認証サーバーへの問い合わせ不要
- **クロスドメイン認証（CORS環境）**: Cookieが使いにくい場面でBearerトークンとして渡せる
- **短命の一回限り操作**: パスワードリセットリンク・メール確認など、数分で失効するトークン
- **M2M認証（Client Credentials）**: サービスアカウント間のAPIアクセス制御

## 採用しないべきケース

- **即時失効が必要なセキュリティ要件**: JWTは有効期限まで無効化できない。アカウント停止・強制ログアウトが即座に効かない
- **モノリスのセッション管理**: ステートフルセッション（サーバーサイドセッション + セッションID Cookie）の方がシンプルで十分
- **長命セッション（weeks/months）**: リフレッシュトークン管理が複雑になり、漏洩時のリスクも高まる
- **ペイロードに機密情報を含む必要がある場合**: デフォルトでは暗号化されていないためJWEが必要になる（複雑度が上がる）

## 実装のアンチパターン

### 1. アルゴリズム検証の欠如（`alg: none` 攻撃）

攻撃者がヘッダーの `alg` を `none` に書き換え、署名なしトークンを送り込める。

```go
// Bad: algを検証していない
token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
    return secretKey, nil  // algがnoneでも通過してしまう
})

// Good: algを明示的に検証する
token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
    if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
        return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
    }
    return secretKey, nil
})
```

### 2. 署名検証のスキップ

```python
# Bad: verify=Falseで署名検証を無効化
payload = jwt.decode(token, options={"verify_signature": False})

# Good: 必ず検証する
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

### 3. ペイロードへの機密情報格納

JWTペイロードはBase64URLデコードするだけで誰でも読める。

```json
// Bad: 機密情報を含む
{
  "user_id": "123",
  "password_hash": "$2b$12$...",
  "credit_card_last4": "1234",
  "internal_role": "superadmin"
}

// Good: 最小限の識別情報のみ
{
  "sub": "user:123",
  "role": "user",
  "exp": 1716000000,
  "iat": 1715996400
}
```

### 4. `localStorage` への保存（XSS脆弱性）

```javascript
// Bad: XSSスクリプトで盗まれる
localStorage.setItem('access_token', jwt);

// Good: HttpOnly Cookieに保存する（JSからアクセス不可）
// Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict
```

### 5. 弱い秘密鍵

HS256のブルートフォース攻撃に対して、短い・推測可能な鍵は危険。

```python
# Bad: 短い・推測可能な鍵
SECRET_KEY = "secret"
SECRET_KEY = "password123"

# Good: 256bit以上のランダムな鍵
SECRET_KEY = secrets.token_hex(32)  # 64文字 = 256bit
```

### 6. 有効期限（`exp`）なしトークン

```json
// Bad: expクレームがなく永続的に有効
{
  "sub": "user:123",
  "role": "admin"
}

// Good: 短い有効期限を設定
{
  "sub": "user:123",
  "role": "admin",
  "exp": 1716000000,
  "iat": 1715996400
}
```

### 7. リフレッシュトークンのローテーションなし

リフレッシュトークンが漏洩しても検知・無効化できない。

```python
# Bad: 毎回同じリフレッシュトークンを返す
def refresh(refresh_token):
    payload = verify(refresh_token)
    return create_access_token(payload["sub"])  # リフレッシュトークンは使い回し

# Good: 使用するたびに新しいリフレッシュトークンを発行し、旧トークンを無効化
def refresh(refresh_token):
    payload = verify_and_invalidate(refresh_token)  # DBで旧トークンを無効化
    new_refresh = create_refresh_token(payload["sub"])
    new_access = create_access_token(payload["sub"])
    return new_access, new_refresh
```

## 実装でトレードオフが生じるケース

### トークン失効問題

| アプローチ | メリット | デメリット |
|-----------|---------|-----------|
| 短い有効期限（5〜15分）+ リフレッシュトークン | 漏洩時のウィンドウが小さい | リフレッシュのラウンドトリップが発生 |
| ブラックリスト（DB管理） | 即時失効が可能 | DBアクセスが必要でステートレスの利点が消える |
| 有効期限を長くする | 実装がシンプル | 漏洩・アカウント停止時のリスクが高い |

**推奨**: アクセストークン15分 + リフレッシュトークン7日（ローテーションあり）。即時失効が必須ならブラックリストを追加するが、その時点でステートフルセッションとのトレードオフを再検討する。

### HS256 vs RS256

| | HS256（対称鍵） | RS256（非対称鍵） |
|-|---------------|----------------|
| 鍵 | 同一の秘密鍵で署名・検証 | 秘密鍵で署名、公開鍵で検証 |
| 適するケース | 単一サービス / 鍵を1か所で管理できる | マイクロサービス / 検証だけしたいサービスが多い |
| リスク | 秘密鍵を共有するサービスが増えると漏洩面が広がる | 鍵のローテーション・配布が複雑 |

### リフレッシュトークンのレースコンディション

複数タブ・デバイスで同時にリフレッシュすると、ローテーション後に片方のリフレッシュトークンが無効化されてログアウトが起きる。

対策の選択肢:
- **リフレッシュウィンドウ**: 旧トークンを数秒間（例: 30秒）有効のまま残す（セキュリティと利便性のトレードオフ）
- **ファミリー管理**: リフレッシュトークンをチェーンで追跡し、同一ファミリーの使用を許容する

### JWTサイズとパフォーマンス

クレームが増えると全リクエストのヘッダーサイズが増大する（Base64エンコード後で通常200〜500バイト、多い場合は1KB超）。

- HTTP/2ヘッダー圧縮（HPACK）でコストは軽減されるが、モバイル・低帯域環境では考慮が必要
- ペイロードのクレームを最小限にするか、重い情報はサーバーサイドセッションに戻すことを検討する

## 関連

- [[saas-authorization-design]] — Auth Middleware内でJWTデコード後にPolicyContextを生成し、PBACで権限リストを構築する設計パターン
