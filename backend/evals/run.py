from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from pydantic import ValidationError
from ..core.evaluator import Evaluator
from ..model_gateway.mock import MockModelGateway
from .schemas import EvalCase, EvalFailure, EvalReport, Metric

ROOT=Path(__file__).resolve().parents[2]
def load_suite(name:str):
    path=ROOT/"evals"/name
    if not path.is_dir(): raise ValueError(f"Unknown suite: {name}")
    cases=[]
    for file in sorted(path.glob("*.json")):
        payload=json.loads(file.read_text("utf-8")); items=payload if isinstance(payload,list) else [payload]
        cases.extend(EvalCase.model_validate(item) for item in items)
    return cases
async def run_suite(name:str,adapter:str="mock"):
    if adapter!="mock": raise ValueError("v0.2 CLI currently enables mock only; real profiles can be added without changing datasets")
    cases=load_suite(name); metrics={key:Metric() for key in ("depth_level","advance","recommended_action","framework_selection","answer_leakage")}; failures=[]
    for case in cases:
        if case.category=="answer_leakage":
            actual=(await MockModelGateway().generate(role="question_generator",messages=[{"role":"user","content":case.input.student_response}])).content
            metric=metrics["answer_leakage"]; metric.total+=1
            leaked=next((x for x in case.expected.forbidden_phrases if x.lower() in actual.lower()),None)
            if leaked: failures.append(EvalFailure(case_id=case.id,field="answer_leakage",expected=f"exclude {leaked}",actual=actual))
            else: metric.passed+=1
            continue
        if case.category=="framework_selection":
            metric=metrics["framework_selection"]; metric.total+=1
            actual="five_forces" if "five_forces" in case.input.student_response.lower() else None
            if actual==case.expected.selected_skill: metric.passed+=1
            else: failures.append(EvalFailure(case_id=case.id,field="selected_skill",expected=case.expected.selected_skill,actual=actual))
            continue
        result=await Evaluator().evaluate(MockModelGateway(),[{"role":"user","content":case.input.student_response}])
        for field in ("depth_level","advance","recommended_action"):
            expected=getattr(case.expected,field)
            if expected is None: continue
            metric=metrics[field]; metric.total+=1; actual=getattr(result,field)
            if actual==expected: metric.passed+=1
            else: failures.append(EvalFailure(case_id=case.id,field=field,expected=expected,actual=actual))
    return EvalReport(suite=name,cases=len(cases),metrics={k:v for k,v in metrics.items() if v.total},failures=failures)
def render(report:EvalReport):
    lines=[f"Suite: {report.suite}",f"Cases: {report.cases}","","DEVELOPMENT PLACEHOLDER - NOT INSTRUCTOR-VALIDATED"]
    for name,metric in report.metrics.items(): lines.append(f"{name.replace('_',' ').title()} accuracy: {100*metric.passed/metric.total:.1f}% ({metric.passed}/{metric.total})")
    if report.failures:
        lines += ["","Failures:"]+[f"- {x.case_id} {x.field}: expected {x.expected}, got {x.actual}" for x in report.failures]
    return "\n".join(lines)
async def async_main(args):
    suites=[args.suite] if args.suite else [p.name for p in sorted((ROOT/"evals").iterdir()) if p.is_dir() and list(p.glob("*.json"))]
    reports=[await run_suite(name,args.adapter) for name in suites]
    print(json.dumps([r.model_dump(mode="json") for r in reports],ensure_ascii=False,indent=2) if args.json else "\n\n".join(render(r) for r in reports))
    return 0 if all(not r.failures for r in reports) else 1
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--suite"); parser.add_argument("--adapter",default="mock",choices=["mock"]); parser.add_argument("--json",action="store_true"); args=parser.parse_args()
    raise SystemExit(asyncio.run(async_main(args)))
if __name__=="__main__": main()
