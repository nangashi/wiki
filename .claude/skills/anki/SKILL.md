---
name: anki
description: insight wikiのページから、概念の説明・事象からの識別・対処の導出を練習する日本語Ankiカードを生成、審査、承認、AnkiConnectへ追加・更新する。全件、指定スラグ、前回以降の差分生成、カード案の確認、既存カードの同期を依頼されたときに使う。
---

# Ankiカード生成

insight wikiを正本として、理解と適用を問う少数のカードを生成する。

## 必須参照

作業開始時に次をすべて読む。

1. `anki/card-criteria.md`
2. `wiki/insight/schema.md`
3. `anki/state.json`（存在する場合）

## フロー

### 1. 対象を決める

- 引数なし: **syncモード**。最初に次を実行し、全ページを `new` / `changed` / `deleted` / `unchanged` に分類する

  ```bash
  python3 .claude/skills/anki/scripts/sync_status.py
  ```

- 指定スラグ: `wiki/insight/pages/<slug>.md` を対象にする
- 全件: `wiki/insight/pages/*.md` を対象にする
- 差分: `new`、`changed`、`deleted` を対象にする。`updated` 日付だけで判定しない

syncモードの分類は次の通り。

- `new`: wikiにあり、stateにない
- `changed`: wikiとstateの両方にあり、contentHashが異なる、またはstateのcriteriaVersionが現行と異なる
- `deleted`: stateにあり、wikiにない
- `unchanged`: wikiとstateの両方にあり、ハッシュと基準versionが一致する

contentHashは、`wiki/insight/pages/<slug>.md` の**ファイル全体のバイト列**に対するSHA-256とする。frontmatter・本文・改行コード・末尾改行をすべて含め、改行変換や空白除去などの正規化は一切行わない。stateには `sha256:<64桁hex>` で保存する。必ず `sync_status.py` と同じ計算を使う。

対象ページと `wiki/insight/index.md` の該当カテゴリを読む。

### 2. カード案を生成・審査する

`anki/card-criteria.md` に厳密に従う。ページごとに1〜3枚とし、網羅しようとしない。

各案について内部で次を検査する。

- 問いが一意か
- タイトル・タグ・出典を隠しても、何の領域・主体・状況についての問いか分かるか
- 抽象語やフレームワーク名だけに文脈を依存していないか
- 文脈を補った結果、答えを問題文に漏らしていないか
- 1概念または1判断か
- ページに根拠があるか
- 概念を細かく分断していないか
- 他の案と重複・干渉しないか
- 事象→対処なら答えに概念名があるか

不合格案は修正または破棄する。ページの核心を理解できない場合はカードを作らず、ページ改善候補として報告する。

新規ページのカード案を次の形式でユーザーに提示する。

```markdown
### <ページタイトル>

**<方向>** `<CardId>`

Q: ...

A: ...

Extra: ...（必要な場合のみ）
```

変更ページは現内容からカード案を作り直し、既存CardIdと突合して次の形式で提示する。

```markdown
### <ページタイトル> — 変更

- **維持** `<CardId>` — 文面・意味とも変更不要
- **文面更新** `<CardId>`
  - Q: `旧` → `新`
  - A: `旧` → `新`
  - 理由: ページ変更との対応
- **stale化** `<CardId>` — 現ページから根拠または必要性が失われた理由
- **新規追加** `<CardId>`
  - Q: ...
  - A: ...
```

同じ意味・想起方向のカードは、表現が変わってもCardIdを維持し、`updateNoteFields` で学習履歴を保全する。CardIdを変えるのは、旧カードとは別の概念または判断を問うカードへ意味が変わった場合だけとする。削除ページは所属する全CardIdのstale化を提示する。

syncモードの冒頭または末尾で分類件数を必ず報告する。`unchanged` は件数のみでよい。

### 3. 承認を得る

新規カード、文面更新、stale化は、Ankiへ書き込む前にユーザーの明示承認を得る。ページ単位・カード単位の部分承認を受け付ける。誤字修正など、ユーザーが一括承認済みの範囲だけ再確認を省略できる。

### 4. Ankiの状態を確認する

Windows版Ankiが起動していることを確認し、次を実行する。

```bash
python3 .claude/skills/anki/scripts/anki_connect.py version
python3 .claude/skills/anki/scripts/anki_connect.py deckNames
python3 .claude/skills/anki/scripts/anki_connect.py modelNames
```

接続はWindows側のloopbackへPowerShell経由で行う。AnkiConnectをLANへbindしない。

書き込み前に以下を確認する。

- `insight` デッキの有無
- `Insight Basic` / `Insight Cloze` の有無とフィールド構成
- `CardId` 検索による既存ノートの有無

ノートタイプが存在しない場合は、承認済みの仕様で作成する。

- `Insight Basic`: `Question`, `Answer`, `Extra`, `Source`, `CardId`
- `Insight Cloze`: `Text`, `Extra`, `Source`, `CardId`（Clozeを実際に使う場合だけ作成）

### 5. 追加または更新する

`CardId` は `<slug>::<direction>::<semantic-key>` とする。文面変更で変えない。

1. `findNotes` で `CardId` を検索する
2. 0件なら `addNote`
3. 1件なら `updateNoteFields` とタグ更新
4. 複数件なら書き込まず、重複を報告する

タグは `insight`、`insight::<カテゴリ>`、`source::<slug>` を付ける。`Source` にはスラグとwiki相対パスを記録する。

生成元から消えたカードは自動削除しない。stale化は、noteへ `stale` タグを追加し、対応カードをsuspendし、stateのstatusを `stale` にする可逆操作を既定とする。削除はユーザーが明示した場合だけ行う。

### 6. stateを更新する

Ankiへの書き込みが成功した場合だけ `anki/state.json` を更新する。最低限、次を保存する。

```json
{
  "criteriaVersion": 1,
  "pages": {
    "<slug>": {
      "contentHash": "sha256:...",
      "sourceUpdated": "YYYY-MM-DD",
      "generatedAt": "ISO-8601",
      "cards": {
        "<CardId>": {"noteId": 123, "status": "active"}
      }
    }
  }
}
```

stateを先に更新しない。部分失敗時は成功した操作だけを記録し、失敗内容を報告する。

## 完了報告

追加・更新・stale・スキップ・失敗の件数とCardIdを示す。AnkiWeb/Androidとの同期操作はAnkiConnect投入とは別であることを明記する。
