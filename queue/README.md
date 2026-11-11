# queue/ — wikiメンテナンスキュー

insightページへの修正を1件1ファイルで管理するキュー。
監査・lint・夜間メンテナンス（`/dream`）で見つかった修正点をここに登録し、機械的に適用できるもの（replace）と人間の判断が要るもの（proposal）を分けて扱う。

- ファイル名: `<target-slug>--<短いkebab-case要約>.md`（拡張子を除いた部分が `id`）
- 同じページへの修正が複数あれば、要約を変えて別ファイルにする

---

## フォーマット

```yaml
---
id: <ファイル名から .md を除いたもの>
target: <対象ページのslug>
kind: replace | proposal
auto: true | false
status: open | proposed | approved | applied | rejected | stale | failed
source: <出所>（例: audit-2026-08-23 P1 / dream-2026-11-12）
old: "<置換前の文字列>"   # kind: replace のみ
new: "<置換後の文字列>"   # kind: replace のみ
applied: <YYYY-MM-DD>      # 適用時に追記
---
本文: 指摘内容と理由（人間が判断の経緯を追えるように書く）
```

| フィールド | 意味 |
|---|---|
| `id` | ファイル名（`.md` 除く）。キュー内で一意 |
| `target` | 対象ページのslug（`wiki/insight/pages/<slug>.md`） |
| `kind` | `replace`: `old` を `new` に置き換えるだけで完了する修正。`proposal`: 文言未確定・複数箇所・構造変更など人間の判断が要る修正 |
| `auto` | `true` なら `/dream` が無人で適用してよい。`kind: replace` のときのみ `true` にできる |
| `status` | 下記ライフサイクル参照 |
| `source` | どの監査・実行で見つかったか |
| `old` / `new` | 固定文字列。`old` は対象ページ内に**ちょうど1回**出現しなければならない（正規表現ではなく文字列一致で判定） |

---

## ステータスのライフサイクル

```
replace(auto):  open ──適用成功──→ applied
                  ├──oldが1回一致しない──→ stale
                  └──適用後にlint悪化──→ failed

proposal:       proposed ──/lint で人間が承認──→ approved（open の auto replace 項目に変換）
                   └──却下──→ rejected
```

- `open`: 適用待ちの replace 項目
- `applied`: 適用済み（`applied: <日付>` を追記）
- `stale`: `old` が対象ページに1回だけ出現する状態でなくなった（ページが先に変更された等）。作り直すか却下する
- `failed`: 適用後に lint の BROKEN / ORPHAN / ALIAS 件数が増えたため差し戻した（本文に1行の理由）
- `proposed`: 人間の判断待ちの proposal
- `approved`: `/lint` で承認され、確定した `old`/`new` を持つ `kind: replace, auto: true, status: open` 項目に変換済み（変換後のファイルの status は `open`）
- `rejected`: 却下（理由を本文に追記）

---

## ルール

1. **`auto: true` の項目を作れるのは、ユーザー本人またはユーザーが承認したセッションのみ。Muse の指摘に由来する項目は、ユーザーの承認前に auto 化しない。** 夜間の `/dream` は auto 項目を決して作らず、proposal を決して適用しない（`/dream` が作れるのは `auto: false` の proposal だけ）
2. **未処理の proposal（`status: proposed`）は20件が上限。** 上限に達している間、新しい指摘は登録しない（先に既存の proposal を `/lint` で消化する）
3. **削除・統合・分割は常に proposal。** replace にしない
4. **replace 項目1件が触れるのは1ページファイルのみ。** 複数ページにまたがる修正は、ページごとに別項目にするか proposal にする
5. **Muse の監査・調査に由来する項目は必ず proposal から始める。** auto への変換はユーザーの承認後だけ（提案者が自分で auto 化しない）
