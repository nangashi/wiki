from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from evaluation_validator import CURRENT_RUBRIC_VERSION as V, validate_text
from design_evaluation_validator import CURRENT_RUBRIC_VERSION as DV
from evaluation_state import queue_rank
D=("核心と推論力","論理と構造","有用性と適用境界","事実基盤","情報設計","日本語の自然さ")
EVALS="wiki/insight/evaluations"
def action(t="修正必須",d="核心と推論力",more=""):
 return f'''### P1: fix
- 種別: {t}
- 観点: {d}
- 対象箇所: 「x」
- 問題: SOURCE_MISSING 問題。
- 改善後に満たす条件: 条件。
- 対応方法: 対応。{more}'''
def ev(states=None,actions="- なし",gate="合格"):
 states=states or {x:"十分" for x in D}
 if gate=="不合格": states={x:"対象外" for x in D}
 rows="\n".join(f"| {x} | {s} | 根拠。 |" for x,s in states.items())
 return f'''# Insight記事評価: sample
- reusability_gate: {gate}
## 再利用性ゲート
- R1: a
- R2: b
- R3: c
- R4: d
## 観点別評価
| 観点 | 状態 | 根拠 |
|---|---|---|
{rows}
## 記事単独読解
- 概念と関係: a
- 現実の見方: a
- 確かさ: a
- 理解が止まった箇所: a
- 適用テスト: a
## 設計との照合
- design_alignment: 合格
- D1: 本文で判断できる。
## 削除候補
- なし
## 対応項目
{actions}
## 良い点
- 良い。\n'''
def design_body(slug,state="十分",actions="- なし"):
 rows="\n".join(f"| {x} | {state if x=='読者・目的' else '十分'} | 根拠。 |" for x in ("読者・目的","読後の到達点","内容と順序","主張と根拠・境界","採用・省略"))
 return f'''# Insight設計評価: {slug}
- reusability_gate: 合格
## 再利用性ゲート
- R1: a
- R2: b
- R3: c
- R4: d
## 観点別評価
| 観点 | 状態 | 根拠 |
|---|---|---|
{rows}
## 対応項目
{actions}
## 良い点
- 明確。\n'''
DESIGN="# Design\n## 読者・目的\n説明。\n## 読後の到達点\n- D1: 判断する。\n- 適用テスト: 新しい状況。→ 判断する。\n## 内容と順序\n説明。\n## 主張と根拠・境界\n説明。\n## 採用・省略\n説明。\n"
def write_design_pair(root,slug,body=None,version=DV):
 """Write a design and its current evaluation; return the evaluation path."""
 from evaluation_state import git_blob
 designs=root/"wiki/insight/designs"; designs.mkdir(parents=True,exist_ok=True); design=designs/f"{slug}.md"
 if not design.exists(): design.write_text(DESIGN,encoding="utf-8")
 history=root/EVALS/slug/"design.md"; history.parent.mkdir(parents=True,exist_ok=True)
 history.write_text(f'''---
target: "wiki/insight/designs/{slug}.md"
target_blob: "{git_blob(design)}"
rubric_version: {version}
evaluator: "claude"
evaluator_model: "opus"
evaluated_at: "2026-01-01T00:00:00Z"
run_id: "design01"
round: 1
---
'''+(body or design_body(slug)),encoding="utf-8")
 return history
def write_rubrics(root):
 refs=root/"wiki/insight/references"; refs.mkdir(parents=True,exist_ok=True)
 (refs/"article-quality-rubric.md").write_text(f"**rubric_version: {V}**\n")
 (refs/"design-quality-rubric.md").write_text(f"**design_rubric_version: {DV}**\n")

class TestValidator(unittest.TestCase):
 def test_optional_passes(self): self.assertTrue(validate_text(ev(actions=action("任意改善")),"sample")["pass"])
 def test_required_prevents_pass(self):
  s={x:"十分" for x in D}; s["事実基盤"]="要対応"
  self.assertFalse(validate_text(ev(s,action("修正必須","事実基盤")),"sample")["pass"])
 def test_research_fields(self):
  s={x:"十分" for x in D}; s["事実基盤"]="要対応"
  self.assertFalse(validate_text(ev(s,action("調査必須","事実基盤")),"sample")["valid"])
 def test_rejected(self): self.assertTrue(validate_text(ev(actions=action("修正必須","再利用性"),gate="不合格"),"sample")["valid"])
 def test_numeric_rejected(self): self.assertFalse(validate_text(ev().replace("- reusability_gate: 合格","- reusability_gate: 合格\n- final_score: 100"),"sample")["valid"])
 def test_other_versions_and_empty_applicability_rejected(self):
  self.assertFalse(validate_text(ev(),"sample",V+1)["valid"])
  self.assertFalse(validate_text(ev(),"sample",V-1)["valid"])
  self.assertFalse(validate_text(ev({x:"対象外" for x in D}),"sample")["valid"])
 def test_deletions_and_application_test(self):
  body=ev()
  self.assertEqual(validate_text(body,"sample")["deletion_count"],0)
  listed=body.replace("## 削除候補\n- なし","## 削除候補\n- 「長い留保」: 核心と適用境界は前節で足りる。")
  self.assertEqual(validate_text(listed,"sample")["deletion_count"],1)
  located=body.replace("## 削除候補\n- なし","## 削除候補\n- 「長い留保」（27行）: 核心と適用境界は前節で足りる。")
  self.assertEqual(validate_text(located,"sample")["deletion_count"],1)
  for bad in (body.replace("## 削除候補\n- なし\n",""),
              body.replace("## 削除候補\n- なし","## 削除候補\n- 長い留保を削る"),
              body.replace("- 適用テスト: a\n",""),
              body.replace("design_alignment: 合格","design_alignment: 未導入")):
   self.assertFalse(validate_text(bad,"sample")["valid"])
 def test_queue_order(self):
  a=[{"slug":"z","research_count":1},{"slug":"b","reusability_gate":"不合格"},{"slug":"a","revision_count":1}]
  self.assertEqual([x["slug"] for x in sorted(a,key=queue_rank)],["b","a","z"])

STAGE1="- 概念と関係: a\n- 現実の見方: a\n- 確かさ: a\n- 理解が止まった箇所: a\n- 適用テスト: a\n"
class StateCliTest(unittest.TestCase):
 def tool(self,root,*args,check=True):
  if args and args[0]=="save":
   if "--stage1" not in args:
    stage1=Path(root)/"stage1.md"
    if not stage1.exists(): stage1.write_text(STAGE1,encoding="utf-8")
    args=(*args,"--stage1",str(stage1))
   if "--round" not in args: args=(*args,"--round","1")
  return subprocess.run([sys.executable,str(HERE/"evaluation_state.py"),*args],cwd=root,text=True,capture_output=True,check=check)
 def setup(self,source="- S1（一次）: https://example.com — 根拠。"):
  tmp=tempfile.TemporaryDirectory(); root=Path(tmp.name); pages=root/"wiki/insight/pages"; pages.mkdir(parents=True)
  write_rubrics(root)
  (pages/"sample.md").write_text(f'''---\ntitle: "t"\n---\n# t\n## 外部ソース\n{source}\n''',encoding="utf-8")
  subprocess.run(["git","init","-q"],cwd=root,check=True)
  self.add_design_pair(root, "sample")
  return tmp,root,pages
 def add_design_pair(self,root,slug): return write_design_pair(root,slug)
 def init_next(self,root,pages):
  manifest=root/".cache/insight-runs/r1/manifest.json"; manifest.parent.mkdir(parents=True,exist_ok=True)
  self.tool(root,"init","--manifest",str(manifest),"--rubric-version",str(V),"--pages-dir",str(pages)); self.tool(root,"next","--manifest",str(manifest),"--limit","1"); return manifest
 def save(self,root,manifest,body,*extra,check=True):
  return self.tool(root,"save","--manifest",str(manifest),"--slug","sample","--body",str(body),*extra,check=check)
 def test_cli_save_overwrites_fixed_file_with_trusted_metadata(self):
  tmp,root,pages=self.setup()
  with tmp:
   manifest=self.init_next(root,pages); b=root/"body.md"; b.write_text(ev())
   self.save(root,manifest,b,"--round","2")
   data=json.loads(manifest.read_text()); self.assertEqual(data["items"][0]["status"],"success"); self.assertTrue(data["items"][0]["target_blob"])
   saved=root/EVALS/"sample/article.md"; text=saved.read_text()
   self.assertEqual(sorted(p.name for p in (root/EVALS/"sample").iterdir()),["article.md","design.md"])
   self.assertIn('evaluator: "claude"\nevaluator_model: "opus"\n',text); self.assertIn("round: 2\n",text)
   self.assertIn("design_evaluation_blob:",text)
   # A second evaluation of the same slug replaces the file instead of accumulating history.
   self.tool(root,"init","--manifest",str(manifest),"--rubric-version",str(V),"--pages-dir",str(pages)); self.tool(root,"next","--manifest",str(manifest))
   self.save(root,manifest,b,"--round","3")
   self.assertIn("round: 3\n",saved.read_text()); self.assertEqual(len(list((root/EVALS/"sample").glob("*.md"))),2)
 def test_evaluator_metadata_accepts_current_only(self):
  tmp,root,pages=self.setup()
  with tmp:
   from evaluation_state import parse_metadata
   history=root/EVALS/"sample/design.md"
   self.assertIsNotNone(parse_metadata(history,"sample","design"))
   original=history.read_text()
   for who,model in (("claude","sonnet"),("codex","gpt-5.6-sol")):
    history.write_text(original.replace('evaluator: "claude"\nevaluator_model: "opus"',f'evaluator: "{who}"\nevaluator_model: "{model}"'))
    self.assertIsNone(parse_metadata(history,"sample","design"),(who,model))
   history.write_text(original.replace("round: 1\n",""))
   self.assertIsNone(parse_metadata(history,"sample","design"))
 def test_source_quality_mandatory_code_and_optional_rejected(self):
  tmp,root,pages=self.setup("外部ソース未確認。")
  with tmp:
   manifest=self.init_next(root,pages); states={x:"十分" for x in D}; states["事実基盤"]="要対応"; b=root/"b.md"
   b.write_text(ev(states,action("修正必須","事実基盤"))); self.save(root,manifest,b)
   tmp2,root2,pages2=self.setup("外部ソース未確認。")
   with tmp2:
    manifest2=self.init_next(root2,pages2); b2=root2/"b.md"; b2.write_text(ev(actions=action("任意改善","事実基盤")))
    self.assertNotEqual(self.save(root2,manifest2,b2,check=False).returncode,0)
   tmp3,root3,pages3=self.setup("外部ソース未確認。")
   with tmp3:
    manifest3=self.init_next(root3,pages3); b3=root3/"b.md"; s={x:"十分" for x in D}; s["核心と推論力"]="要対応"; b3.write_text(ev(s,action("修正必須","核心と推論力")))
    self.assertNotEqual(self.save(root3,manifest3,b3,check=False).returncode,0)
 def test_structural_sources_and_old_runs_refused(self):
  tmp,root,pages=self.setup("- S1（一次） https://example.com — 根拠。")
  with tmp:
   manifest=self.init_next(root,pages); b=root/"b.md"; b.write_text(ev())
   self.assertNotEqual(self.save(root,manifest,b,check=False).returncode,0)
   self.assertFalse((root/EVALS/"sample/article.md").exists())
   self.assertNotEqual(self.tool(root,"init","--manifest",str(root/"old.json"),"--rubric-version",str(V-1),"--pages-dir",str(pages),check=False).returncode,0)
   self.assertNotEqual(self.tool(root,"init","--manifest",str(root/"future.json"),"--rubric-version",str(V+1),"--pages-dir",str(pages),check=False).returncode,0)
   d=json.loads(manifest.read_text()); d["rubric_version"]=2; manifest.write_text(json.dumps(d)); self.assertNotEqual(self.tool(root,"resume","--manifest",str(manifest),check=False).returncode,0)
 def test_invalid_legacy_and_stale_are_classified(self):
  tmp,root,pages=self.setup()
  with tmp:
   manifest=self.init_next(root,pages); b=root/"b.md"; b.write_text(ev()); self.save(root,manifest,b)
   (pages/"sample.md").write_text((pages/"sample.md").read_text()+"変更\n")
   out=root/"n.json"; self.tool(root,"normalize","--pages-dir",str(pages),"--rubric-version",str(V),"--output",str(out))
   data=json.loads(out.read_text()); self.assertEqual(data["records"][0]["status"],"changed"); self.assertFalse(data["improvement_queue"]); self.assertTrue(data["reevaluation_required"])
   article=root/EVALS/"sample/article.md"
   article.write_text(article.read_text().replace(f"rubric_version: {V}\n",f"rubric_version: {V-1}\n"))
   data=json.loads(self.tool(root,"normalize","--pages-dir",str(pages)).stdout)
   self.assertEqual(data["records"][0]["status"],"legacy"); self.assertFalse(data["invalid_history"])
   article.write_text("bad")
   data=json.loads(self.tool(root,"normalize","--pages-dir",str(pages)).stdout)
   self.assertEqual(data["records"][0]["status"],"missing"); self.assertEqual(data["invalid_history"][0]["reason"],"metadata")
 def test_save_rejects_missing_or_mismatched_stage1(self):
  tmp,root,pages=self.setup()
  with tmp:
   manifest=self.init_next(root,pages); b=root/"b.md"; b.write_text(ev())
   other=root/"other.md"; other.write_text(STAGE1.replace("確かさ: a","確かさ: b"),encoding="utf-8")
   base=("save","--manifest",str(manifest),"--slug","sample","--body",str(b),"--round","1")
   self.assertNotEqual(self.tool(root,*base,"--stage1",str(other),check=False).returncode,0)
   missing=subprocess.run([sys.executable,str(HERE/"evaluation_state.py"),*base],cwd=root,text=True,capture_output=True)
   self.assertNotEqual(missing.returncode,0)
   self.assertFalse((root/EVALS/"sample/article.md").exists())
   self.tool(root,*base)
   self.assertEqual(json.loads(manifest.read_text())["items"][0]["status"],"success")
 def test_normalize_marks_an_article_without_a_design_as_required(self):
  tmp,root,pages=self.setup()
  with tmp:
   (root/"wiki/insight/designs/sample.md").unlink()
   out=root/"n.json"; self.tool(root,"normalize","--pages-dir",str(pages),"--evaluations-root",str(root/"empty"),"--output",str(out))
   data=json.loads(out.read_text()); self.assertEqual(data["records"][0]["design_state"],"required"); self.assertEqual(data["process_distribution"]["required"],1); self.assertEqual(data["design_reevaluation_required"],[{"slug":"sample","status":"missing"}])
 def test_evidence_appends_and_rejects_bad_bodies(self):
  tmp,root,pages=self.setup()
  with tmp:
   body=root/"ev.md"; body.write_text("# 外部検証: sample\n## 確認済み\n- 主張 / 根拠 / https://example.com\n## 未確認\n- なし\n## 誤り\n- なし\n",encoding="utf-8")
   args=("evidence","--slug","sample","--body",str(body),"--target","wiki/insight/pages/sample.md")
   self.tool(root,*args,"--run-id","evidence01","--verified-at","2026-01-01T00:00:00Z")
   self.tool(root,*args,"--run-id","evidence02")
   text=(root/"wiki/insight/evidence/sample.md").read_text()
   self.assertTrue(text.startswith("# 外部検証記録: sample\n")); self.assertEqual(text.count("### 確認済み"),2)
   self.assertIn("## 2026-01-01T00:00:00Z run=evidence01\n",text)
   self.assertNotEqual(self.tool(root,*args,"--run-id","evidence01",check=False).returncode,0)
   body.write_text("# 外部検証: sample\n## 確認済み\n- x\n## 誤り\n- なし\n",encoding="utf-8")
   self.assertNotEqual(self.tool(root,*args,check=False).returncode,0)
   self.assertNotEqual(self.tool(root,"evidence","--slug","sample","--body",str(body),"--target","wiki/insight/pages/other.md",check=False).returncode,0)

class DesignReferenceTest(unittest.TestCase):
 def test_missing_evaluation_and_evidence_references_are_listed(self):
  from check import missing_design_references
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); designs=root/"wiki/insight/designs"; designs.mkdir(parents=True)
   kept=root/"wiki/insight/evidence/a.md"; kept.parent.mkdir(parents=True); kept.write_text("x")
   (designs/"a.md").write_text("証拠 [evidence/a.md](../evidence/a.md) と wiki/insight/evidence/a.md、欠落 evaluations/insight/a/external/gone.md と ../evidence/b.md。\n",encoding="utf-8")
   self.assertEqual(missing_design_references(root,designs),[("a","../evidence/b.md"),("a","evaluations/insight/a/external/gone.md")])
if __name__=="__main__": unittest.main()
