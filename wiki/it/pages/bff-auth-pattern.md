---
title: "BFFパターンによる認証トークン配置設計"
type: "リファレンス型"
sources:
  - "https://zenn.dev/khale/articles/web-session-jwt-cookie-history"
created: "2026-06-13"
updated: "2026-06-13"
---

# BFFパターンによる認証トークン配置設計

## 概要

BFF（Backend For Frontend）を用いて、ブラウザ↔バックエンド間の認証境界にはHttpOnly Cookieを、BFF↔外部API・マイクロサービス間の通信にはJWT/OAuth2トークンを置く、認証トークンの配置設計パターン。Next.js・Nuxt.js・SvelteKitなどフルスタックフレームワークでサーバー機能が使えるようになったことで普及した。最大の優位性は、ブラウザにトークンを一切露出させないことでXSSによるトークン窃取リスクを構造的に排除しつつ、バックエンド間連携ではJWTのステートレス検証の利点をそのまま維持できる点にある。核心は「認証境界ごとに適したトークン形式を選ぶ」層別設計であり、Cookieは即時失効・CSRF対策に強くブラウザ境界に適し、JWTはDBアクセスなしで検証できるためサービス間連携に適するという特性の違いをアーキテクチャ上に明示する。

## 他の認証アーキテクチャとの比較

| | BFFパターン（Cookie+JWT分離） | SPA + localStorage直接JWT | モノリス・セッションCookieのみ |
|---|---|---|---|
| 主な用途 | フルスタックFWでの外部API/マイクロサービス連携 | 別ドメインAPIと通信するSPA | サーバーサイドレンダリングのモノリス |
| XSS耐性 | ◎ トークンがJSから不可視 | △ localStorageはJSから読み取れる | ◎ HttpOnly Cookieで保護 |
| 即時失効 | ◎ サーバー側でセッション破棄すれば即時 | ✗ exp待ちかブラックリストが必要 | ◎ サーバー側でセッション削除すれば即時 |
| マイクロサービス/外部API連携 | ◎ BFFがJWTでステートレス検証 | ◎ JWTを直接Bearerで送信できる | ✗ Cookieはクロスドメインで送れない |
| 実装複雑度 | 中（BFF層・トークン変換が必要） | 低（直接通信） | 低（従来型構成） |

## 採用すべきケース

- フルスタックフレームワーク（Next.js/Nuxt/SvelteKit等）でサーバーサイドAPIルート/Server Actionsが使える
- バックエンドが複数の外部API・マイクロサービスと連携し、それらの認証にJWTが必要
- XSS耐性と即時失効を両立したい（JWTのみでは即時失効が困難、Cookieのみではマイクロサービス連携が困難）

## 採用しないべきケース

- 純粋なSPA構成でサーバー機能を持てない（BFFを置く場所がない）場合
- 外部API連携が一切なく単一バックエンドのみの場合: モノリスのセッションCookieで十分で、JWTへの変換は不要な複雑さを増やす

## 実装のアンチパターン

### 1. session()コールバックでアクセストークンをクライアントに返す（NextAuth）

NextAuthの`session()`コールバックでアクセストークンをそのままクライアントに返すと、HttpOnly Cookieによる保護が無意味になる（トークンがクライアントのJSオブジェクトとして露出する）。

```typescript
// Bad: session callbackでaccessTokenを返す
callbacks: {
  session({ session, token }) {
    session.accessToken = token.accessToken // クライアントに露出してしまう
    return session
  }
}

// Good: トークンは暗号化JWE Cookieに保持し、サーバー専用関数からのみ取得する
import "server-only" // クライアントバンドルに含まれないことを保証

export async function getAccessToken() {
  const token = await getToken({ req, secret, encryption: true })
  return token.accessToken
}
```

## 実装でトレードオフが生じるケース

### Cookie復権は「2005年への後退」ではない

サードパーティCookie規制（Safari ITP 2017・Chrome SameSite 2020）とSPAの普及により、一度はCookieセッションが廃れlocalStorage+JWTが主流になった。しかしBFFパターンでの「Cookieの復権」は、モノリス時代のサーバーサイドセッションへの単純な後退ではない。分散Redis・エッジランタイム・OIDCプロバイダー・マイクロサービス間のJWT/mTLS認証など内部実装は全く異なるアーキテクチャ上に、「ブラウザ境界=Cookie」という同じ表面パターンが再構築されている。

| 観点 | 旧来のCookieセッション（〜2010年代） | BFFパターンでのCookie復権 |
|------|------------------------------|------------------------|
| セッション保存先 | アプリサーバーのメモリ/DB | 分散Redis/エッジKVストア |
| バックエンド構成 | モノリス | BFF + 複数マイクロサービス（JWT/mTLS） |
| サービス間認証 | 不要（単一サーバー） | JWT/OAuth2/Service Mesh |

**推奨**: 既存実装がCookieからJWTへ移行済みの場合、再度Cookieに戻す判断を「退化」と捉えず、BFF層を導入できるか（フルスタックフレームワークへの移行可否）を判断基準にする。

## 関連

- [[jwt]] — BFFと外部API/マイクロサービス間で使われるトークン形式。本パターンではブラウザ境界のCookieと使い分ける
- [[saas-authorization-design]] — Auth Middleware内でJWTをデコードしてPolicyContextを生成する流れは、BFF↔API間の認証処理と連携する
