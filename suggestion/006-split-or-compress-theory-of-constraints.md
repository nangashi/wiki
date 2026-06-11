# 提案: [[theory-of-constraints]] を分割または圧縮する

## 対象

- `wiki/insight/pages/theory-of-constraints.md`

## 判定

粒度過大。単一ページ内に TOC の核心、会計パラダイム、5つの集中ステップ、DBR、DevOps適用、翻訳逸話が混在している。

## 根拠

lint の粒度メトリクスで `LARGE(3296chars)` が検出された。本文を読むと、単なる長さだけでなく、複数の独立概念がページ内に入っている。

特に「5つの集中ステップ」と「ドラム・バッファ・ロープ」は、TOC の応用実装として独立して説明できる。現在のページは本質審査としては強いが、参照性が落ちている。

## 改善案

次のいずれかを行う。

1. 圧縮案: `theory-of-constraints` は「制約が全体スループットを決める」という核心と評価軸転換に絞り、実装詳細を短くする。
2. 分割案: `toc-five-focusing-steps.md` と `drum-buffer-rope.md` を作成し、現ページから詳細を移す。

分割する場合、`theory-of-constraints` は上位概念として残し、関連に新規ページへのリンクを追加する。
