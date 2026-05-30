---
title: "AIコーディングのESLint制約設計（eslint-plugin-boundaries含む）"
sources:
  - "https://zenn.dev/erukiti/articles/2512-full-ai-cofing"
created: "2026-05-23"
updated: "2026-05-23"
---

# AIコーディングのESLint制約設計（eslint-plugin-boundaries含む）

## 概要

LLMの非決定的振る舞い（同一プロンプトで毎回異なるスタイルが生成される）と知識と活用の乖離（SOLID原則を知っているが適用しない）を補正する最有効手段は、ESLintで「書いてよいコードの空間」を制約すること。9ヶ月以上のコーディングエージェント実運用から得られた知見。

## 詳細

### 背景：環境整備優先の原則

「指示を増やせば未知は減るが矛盾は増える」——プロンプトで網羅しようとするほど指示間の矛盾が増加し、LLMの恣意的解釈を招く。代わりに、ツールレベルでLLMが誤った実装を「できない」状態を作ることがコーディング品質の根本的な保証になる。

このESLint制約は[[ai-context-management]]で説明するLLMの非決定論的振る舞いと知識-活用乖離への最有効な対処手段として機能する。

### 推奨スタック（TypeScript）

```
TypeScript（必須）
Node.js LTS（v22, v24）
pnpm
eslint（厳密ルール）
vitest
husky
```

`bun` / `bun test` は現時点で「茨の道」のため非推奨。

### 禁止すべきESLintルール

| ルール対象 | 理由 |
|-----------|------|
| `enum` 禁止 | LLMがenumを好むが型安全性が低い |
| `class` 原則禁止 | 副作用・継承の連鎖をLLMが見落とす |
| `throw` 禁止 | Result型で明示的エラー伝播を強制 |
| `Promise` 返却禁止 | Result型を使う（async/awaitへの統一） |
| サブパスimport禁止 | 依存関係の追跡困難化を防ぐ |
| barrel export禁止 | re-exportによる依存関係の隠蔽を防ぐ |

### eslint-plugin-boundariesで依存方向を強制

レイヤー構造（`domain → usecase → infrastructure`）の依存方向をlinterレベルで強制する。LLMが「知っているが適用しない」問題を構造的に解決する。

```js
// .eslintrc.js
{
  "rules": {
    "boundaries/element-types": [2, {
      "default": "disallow",
      "rules": [
        { "from": "domain", "allow": ["domain"] },
        { "from": "usecase", "allow": ["domain", "usecase"] },
        { "from": "infrastructure", "allow": ["domain", "usecase", "infrastructure"] }
      ]
    }]
  }
}
```

### テスト戦略（AIコーディング文脈）

「テスティングトロフィーは人間時代の考え方。AIコーディングでは結合テストがすべて」

- 結合テスト（DBへの実際の読み書き含む）を最重要視
- 単体テストは最小限（LLMの「自作自演」による偽陰性を避ける）
- カバレッジ100%を目標
- エラーケースを必ず網羅

### TSDocコメント戦略

```typescript
/**
 * 注文を確定して決済を実行する。
 * @param orderId - 対象の注文ID
 * @returns 決済結果。失敗時は Err(PaymentError)
 * @remarks
 * 冪等性あり。同一orderIdで複数回呼んでも2重決済にならない。
 * カード残高不足は card_declined、与信枠超過は credit_limit が返る。
 */
```

- 「プロジェクト外のジュニアエンジニアにも読める」基準で書く
- テストコードの前提条件・検証項目を日本語でコメント化
- サンプルデータは実名に近い文字列または明確な日本語を使用

### レビューパターン

「まっさらなジュニアエンジニア」として全前提を疑う問いを投げる（LLMのコンテキスト絶対化を外部から解体するアプローチ）:
- 「このassumeは本当に保証されているか」
- 「このデフォルト値の根拠は何か」
- 「このエラーは握りつぶされていないか」

## 関連
- [[ai-context-management]] — このツールチェーンが対処するLLMの4限界パターンと指示設計の原則
