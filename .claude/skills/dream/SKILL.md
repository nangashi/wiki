---
description: 夜間メンテナンス（キュー消化・本質サンプル再判定・再審査バックフィル）
---

# /dream スキル

夜間に無人で実行するメンテナンス。`queue/` の auto 項目を少量だけ適用し、本質サンプリング監査と再審査バックフィルを行い、結果を `dream/auto` ブランチに積む。
`dream/auto` は週1回Museがレビューして main にマージする。このスキルは main に直接書き込まない。

キューの形式・ステータス・ルールは `queue/README.md` を正本とする。

## 絶対に守ること

- **proposal を適用しない。** 削除・統合・分割も行わない（それらは常に proposal であり、`/lint` で人間が判断する）
- **`auto: true` の項目を作らない。** このスキルが作れるのは `kind: proposal, auto: false, status: proposed` の項目だけ
- **触ってよいファイルは `wiki/insight/pages/*.md` と `queue/*.md`（`queue/README.md` を除く）のみ。** `.claude/`・`wiki/insight/index.md`・`schema.md`・`references/` などは変更しない
- 上限: replace 適用は1晩 **最大2件**、再審査バックフィルは1晩 **最大2ページ**、未処理 proposal（`status: proposed`）は **20件まで**
- 対話でユーザーに確認を求めない（無人実行）。判断に迷ったら「何もしない」側に倒す

以下 `<today>` は実行日の `YYYY-MM-DD`、`<version>` は `wiki/insight/references/essence-review-criteria.md` 冒頭の `version: N` の N。

---

## ステップ0: 前提条件

1. `git status --porcelain` を実行し、出力が空であることを確認する（`.tmp/` は `.gitignore` 済みなので出力に現れない）。空でなければ中断する（`reason=dirty-tree`）
2. 現在のブランチ名を `<start-branch>` として記録する（終了時に戻るため）
3. `git fetch origin`
4. `dream/auto` に移動する:
   - ローカルに `dream/auto` があれば `git checkout dream/auto`
   - ローカルになく `origin/dream/auto` があれば `git checkout -b dream/auto origin/dream/auto`
   - どちらもなければ `git checkout -b dream/auto origin/main`
5. `git merge --no-edit origin/main` を実行する。コンフリクトしたら `git merge --abort` → `git checkout <start-branch>` → 中断する（`reason=merge-conflict`）

**中断時の出力**（中断した場合はここで終了し、以降のステップを実行しない）:

```
DREAM_ABORT reason=<dirty-tree|merge-conflict|other> branch=dream/auto
DREAM_SUMMARY applied=0 proposed=0 stale=0 failed=0 queue_open=? queue_proposed=? branch=dream/auto
```

（`queue_open` / `queue_proposed` は数えられれば数え、数えられなければ `?`）

---

## ステップ1: ベースライン計測

```bash
bash .claude/skills/lint/lint-check.sh --collection insight:wiki/insight/pages > .tmp/dream-lint-base.txt
```

次の3つの件数を記録する（各チェックの `COUNT:` 行と同値。行頭一致で数えると `LOW_VALUE ... TINY_ORPHAN` を誤カウントしない）:

| 指標 | 数え方 |
|---|---|
| BROKEN | `grep -c '^BROKEN ' .tmp/dream-lint-base.txt` |
| ALIAS | `grep -c '^ALIAS ' .tmp/dream-lint-base.txt` |
| ORPHAN | `grep -c '^ORPHAN ' .tmp/dream-lint-base.txt` |

`SAMPLE` 行（ステップ3で使う）と `STALE_REVIEW` 行（ステップ4で使う）もこの出力から取る。SAMPLE はランダムなので比較に使わない。METRICS・MISSING_LINK はノイズとして無視する。

---

## ステップ2: キュー消化（replace のみ、最大2件）

### 対象の選定

`queue/*.md`（`README.md` を除く）のうち、frontmatter が **`status: open` かつ `auto: true` かつ `kind: replace`** のものを `id` の昇順に並べ、先頭から **最大2件** を処理する。条件を1つでも満たさない項目には触れない。

### 各項目の処理

対象ページは `wiki/insight/pages/<target>.md`。

1. **一致確認**: `old` を `Write` ツールで `.tmp/dream-old.txt` に書き出し（シェルのクォート崩れを避けるため）、固定文字列で出現回数を数える:
   ```bash
   grep -o -F -f .tmp/dream-old.txt wiki/insight/pages/<target>.md | wc -l
   ```
   結果が **ちょうど1でなければ**（0回・2回以上・ページが存在しない）、項目の `status:` を `stale` に書き換え、本文末尾に `- <today> dream: old の出現回数が N 回のため stale` を追記して次の項目へ進む（stale K に加算）
2. **置換**: `Edit` ツールで `old_string = old`、`new_string = new` として置換する（`Edit` は一意一致を要求するので二重の安全策になる）。`old`/`new` は YAML の値をそのまま使い、文言を一切変えない
3. **frontmatter 更新**（同じページ）:
   - `updated:` を `"<today>"` に書き換える（既存の引用符付き形式を保つ）
   - `reviewed:` 行があれば **削除する**（内容が変わったので再審査が必要。次回以降のバックフィル対象になる）
4. **検証**: lint を再実行し、BROKEN / ALIAS / ORPHAN を同じ方法で数える
   ```bash
   bash .claude/skills/lint/lint-check.sh --collection insight:wiki/insight/pages > .tmp/dream-lint-after.txt
   ```
   - いずれかがベースラインより **増えていたら**: `git restore wiki/insight/pages/<target>.md` でページを戻し、項目の `status:` を `failed` に書き換え、本文末尾に `- <today> dream: 適用後に <指標> が <前>→<後> に増えたため差し戻し` を1行追記する（failed F に加算）。次の項目へ進む
   - 増えていなければ成功: 項目の `status:` を `applied` に書き換え、frontmatter に `applied: <today>` を追記する（applied N に加算）。ベースラインは更新しない（常に初回計測と比較する）

---

## ステップ3: 本質サンプリング監査

1. `wiki/insight/references/essence-review-criteria.md` を読む
2. ステップ1の出力の `SAMPLE` 行のslug（3件）について、各ページを読み、C1（核心の一文性）・C2（核心から現象が逆算できる）・C3（対処が本質への干渉として説明されている。対処・実践セクションがある場合のみ）を判定する
3. **合格**: 何もしない
4. **不合格**: 下記「proposal の登録」に従って proposal を作る（proposed M に加算）。ページ自体は修正しない

---

## ステップ4: 再審査バックフィル（最大2ページ）

1. ステップ1の出力の `STALE_REVIEW` 行から、**このステップ2で変更したページを除き**、slug の昇順で **最大2ページ** を選ぶ（同じ晩に「適用した本人が即再審査する」ことを避け、差分のレビューを分けるため）
2. 各ページを `essence-review-criteria.md` の C1〜C3 で審査する
3. **合格**: frontmatter の `reviewed:` を `<version>` にする（行がなければ `updated:` の次の行に追加）。`updated:` を `"<today>"` に書き換える。本文は変更しない
4. **不合格**: `reviewed:` は変更せず、下記「proposal の登録」に従って proposal を作る（proposed M に加算）

---

## proposal の登録（ステップ3・4共通）

1. **上限確認**: `queue/*.md` のうち `status: proposed` の件数を数える。**20件以上なら登録しない**（スキップしたことは最終出力の注記に残す）
2. **重複確認**: 同じ `target` で `status: proposed` の項目が既にあり、内容が同じ指摘なら登録しない
3. **ファイル作成**: `queue/<slug>--essence-<不合格基準>-fail.md`（例: `--essence-c2-fail`。同名ファイルが既にあれば末尾に `-<today>` を付ける）

```markdown
---
id: <ファイル名から .md を除いたもの>
target: <slug>
kind: proposal
auto: false
status: proposed
source: dream-<today>
---

**<slug>** — 本質審査 不合格（<C1|C2|C3>、criteria version <version>）

- 判定の経緯: <サンプリング監査 / 再審査バックフィル>
- 不合格理由: <どの記述がどの基準を満たしていないか。該当箇所を引用する>
- 改善の方向: <1〜2行。具体的な文言は確定させない（確定は /lint で人間が行う）>
```

**`old`/`new` を書かない。`auto: true` にしない。** 文言の確定と auto 化は `/lint` で人間が行う。

---

## ステップ5: 終了処理

1. `git status --porcelain` で変更ファイルを確認する。`wiki/insight/pages/` と `queue/` 以外のパスが含まれていたら、コミットせずに `git stash -u` で退避し、`DREAM_ABORT reason=unexpected-change` を出して `<start-branch>` に戻って終了する
2. 変更があれば:
   ```bash
   git add -A
   git commit -m "dream: <today> applied N, proposed M, stale K"
   git push -u origin dream/auto
   ```
   push に失敗した場合はコミットを残したまま、最終出力の注記に `push failed` と書く
3. 変更がなければ（何も処理せず何も変わらなければ）コミットしない
4. `git checkout <start-branch>` で元のブランチに戻る
5. 最終出力として、次の要約ブロックを **必ず** 出力する（値はすべて整数）:

```
DREAM_SUMMARY applied=N proposed=M stale=K failed=F queue_open=X queue_proposed=Y branch=dream/auto
```

- `applied` / `proposed` / `stale` / `failed`: この実行で増えた件数
- `queue_open`: 実行終了時点の `status: open` の項目数
- `queue_proposed`: 実行終了時点の `status: proposed` の項目数
- 何も処理せず何も変わらなかった場合も、すべて0（`queue_*` は実数）で出力する

要約ブロックの後に、人間向けの短い注記（適用した項目id、stale/failed の理由、上限で登録を見送った指摘、サンプル監査の合否）を箇条書きで付けてよい。
