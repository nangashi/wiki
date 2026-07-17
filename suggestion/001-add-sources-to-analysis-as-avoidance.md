---
status: applied
target: analysis-as-avoidance
created: "2026-05-30"
---

# 提案: [[analysis-as-avoidance]] に sources を追加する

## 対象

- `wiki/insight/pages/analysis-as-avoidance.md`

## 判定

不合格。frontmatter に `sources` がない。

## 根拠

`wiki/insight/schema.md` は frontmatter の標準項目として `title`・`sources`・`created`・`updated` を定義している。本文では Anderson (2003)、Kunda (1990)、Schwartz (2004) など研究者名と年が出ているが、参照元が frontmatter に記録されていないため、出典検証ができない。

## 改善案

`sources` を追加し、少なくとも本文で参照している一次または準一次ソースを記録する。

例:

```yaml
sources:
  - "paper:Anderson, C. J. (2003). The Psychology of Doing Nothing"
  - "paper:Kunda, Z. (1990). The Case for Motivated Reasoning"
  - "book:選択のパラドックス（バリー・シュワルツ）"
```

必要なら Web で書誌情報を確認して、URL も併記する。
