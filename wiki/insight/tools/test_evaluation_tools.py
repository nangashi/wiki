from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from evaluation_validator import validate_text
from evaluation_state import queue_rank
D=("核心と推論力","論理と構造","有用性と適用境界","事実基盤","情報設計","日本語の自然さ")
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
## 対応項目
{actions}
## 良い点
- 良い。\n'''
class TestV3(unittest.TestCase):
 def test_optional_passes(self): self.assertTrue(validate_text(ev(actions=action("任意改善")),"sample")["pass"])
 def test_required_prevents_pass(self):
  s={x:"十分" for x in D}; s["事実基盤"]="要対応"
  self.assertFalse(validate_text(ev(s,action("修正必須","事実基盤")),"sample")["pass"])
 def test_research_fields(self):
  s={x:"十分" for x in D}; s["事実基盤"]="要対応"
  self.assertFalse(validate_text(ev(s,action("調査必須","事実基盤")),"sample")["valid"])
 def test_rejected(self): self.assertTrue(validate_text(ev(actions=action("修正必須","再利用性"),gate="不合格"),"sample")["valid"])
 def test_numeric_rejected(self): self.assertFalse(validate_text(ev().replace("- reusability_gate: 合格","- reusability_gate: 合格\n- final_score: 100"),"sample")["valid"])
 def test_future_version_and_empty_applicability_rejected(self):
  self.assertFalse(validate_text(ev(),"sample",6)["valid"])
  self.assertFalse(validate_text(ev({x:"対象外" for x in D}),"sample")["valid"])
 def test_qualitative_history_remains_readable(self):
  for version in (3, 4):
   history=f"---\nrubric_version: {version}\n---\n"+ev()
   self.assertTrue(validate_text(history,"sample")["valid"])
 def test_legacy_version_routes_to_frozen_validator(self):
  legacy=validate_text("# Insight記事評価: sample\n", "sample", 2)
  self.assertFalse(legacy["valid"])
  self.assertIn("raw_score",legacy)
 def test_queue_order(self):
  a=[{"slug":"z","research_count":1},{"slug":"b","reusability_gate":"不合格"},{"slug":"a","revision_count":1}]
  self.assertEqual([x["slug"] for x in sorted(a,key=queue_rank)],["b","a","z"])
class StateCliTest(unittest.TestCase):
 def tool(self,root,*args,check=True):
  return subprocess.run([sys.executable,str(HERE/"evaluation_state.py"),*args],cwd=root,text=True,capture_output=True,check=check)
 def setup(self,source="- S1（一次）: https://example.com — 根拠。"):
  tmp=tempfile.TemporaryDirectory(); root=Path(tmp.name); pages=root/"wiki/insight/pages"; pages.mkdir(parents=True)
  (pages/"sample.md").write_text(f'''---\ntitle: "t"\n---\n# t\n## 外部ソース\n{source}\n''',encoding="utf-8")
  subprocess.run(["git","init","-q"],cwd=root,check=True); return tmp,root,pages
 def init_next(self,root,pages):
  manifest=root/"manifest.json"; self.tool(root,"init","--manifest",str(manifest),"--rubric-version","5","--pages-dir",str(pages)); self.tool(root,"next","--manifest",str(manifest),"--limit","1"); return manifest
 def test_cli_save_records_claimed_hash(self):
  tmp,root,pages=self.setup()
  with tmp:
   manifest=self.init_next(root,pages); b=root/"body.md"; b.write_text(ev())
   self.tool(root,"save","--manifest",str(manifest),"--slug","sample","--body",str(b),"--evaluations-root",str(root/"eval"))
   data=json.loads(manifest.read_text()); self.assertEqual(data["items"][0]["status"],"success"); self.assertTrue(data["items"][0]["target_blob"])
 def test_source_quality_mandatory_code_and_optional_rejected(self):
  tmp,root,pages=self.setup("外部ソース未確認。")
  with tmp:
   manifest=self.init_next(root,pages); states={x:"十分" for x in D}; states["事実基盤"]="要対応"; b=root/"b.md"
   b.write_text(ev(states,action("修正必須","事実基盤"))); self.tool(root,"save","--manifest",str(manifest),"--slug","sample","--body",str(b),"--evaluations-root",str(root/"eval"))
   tmp2,root2,pages2=self.setup("外部ソース未確認。")
   with tmp2:
    manifest2=self.init_next(root2,pages2); b2=root2/"b.md"; b2.write_text(ev(actions=action("任意改善","事実基盤")))
    self.assertNotEqual(self.tool(root2,"save","--manifest",str(manifest2),"--slug","sample","--body",str(b2),"--evaluations-root",str(root2/"eval"),check=False).returncode,0)
   tmp3,root3,pages3=self.setup("外部ソース未確認。")
   with tmp3:
    manifest3=self.init_next(root3,pages3); b3=root3/"b.md"; s={x:"十分" for x in D}; s["核心と推論力"]="要対応"; b3.write_text(ev(s,action("修正必須","核心と推論力")))
    self.assertNotEqual(self.tool(root3,"save","--manifest",str(manifest3),"--slug","sample","--body",str(b3),"--evaluations-root",str(root3/"eval"),check=False).returncode,0)
 def test_structural_sources_and_old_runs_refused(self):
  tmp,root,pages=self.setup("- S1（一次） https://example.com — 根拠。")
  with tmp:
   manifest=self.init_next(root,pages); b=root/"b.md"; b.write_text(ev())
   self.assertNotEqual(self.tool(root,"save","--manifest",str(manifest),"--slug","sample","--body",str(b),"--evaluations-root",str(root/"eval"),check=False).returncode,0)
   self.assertNotEqual(self.tool(root,"init","--manifest",str(root/"old.json"),"--rubric-version","4","--pages-dir",str(pages),check=False).returncode,0)
   self.assertNotEqual(self.tool(root,"init","--manifest",str(root/"future.json"),"--rubric-version","6","--pages-dir",str(pages),check=False).returncode,0)
   d=json.loads(manifest.read_text()); d["rubric_version"]=2; manifest.write_text(json.dumps(d)); self.assertNotEqual(self.tool(root,"resume","--manifest",str(manifest),check=False).returncode,0)
 def test_mixed_history_and_stale_excluded(self):
  tmp,root,pages=self.setup()
  with tmp:
   manifest=self.init_next(root,pages); b=root/"b.md"; b.write_text(ev()); self.tool(root,"save","--manifest",str(manifest),"--slug","sample","--body",str(b),"--evaluations-root",str(root/"eval"),"--evaluated-at","2026-01-01T00:00:00Z","--evaluation-run-id","abcdefgh")
   # A malformed historical file is reported; a changed page is re-evaluation-required.
   bad=root/"eval/sample/20260102T000000Z-v4-bcdefghi.md"; bad.write_text("bad")
   (pages/"sample.md").write_text((pages/"sample.md").read_text()+"変更\n")
   out=root/"n.json"; self.tool(root,"normalize","--pages-dir",str(pages),"--evaluations-root",str(root/"eval"),"--rubric-version","5","--output",str(out))
   data=json.loads(out.read_text()); self.assertEqual(data["records"][0]["status"],"changed"); self.assertFalse(data["improvement_queue"]); self.assertTrue(data["invalid_history"]); self.assertTrue(data["reevaluation_required"])

if __name__=="__main__": unittest.main()
