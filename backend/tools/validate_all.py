from pathlib import Path
from .validation import validate_case, validate_skill
def main():
    root=Path.cwd(); reports=[]
    for manifest in sorted((root/"skills").glob("*/*/manifest.yaml")): reports.append(validate_skill(manifest.parent))
    for manifest in sorted((root/"cases").glob("*/manifest.yaml")): reports.append(validate_case(manifest.parent,root))
    for report in reports: print(report.render(),"\n")
    skills=sum("skill:" in r.subject and r.valid for r in reports); cases=sum("case:" in r.subject and r.valid for r in reports); instructors=len(list((root/"instructors").glob("*/profile.yaml")))
    print(f"Skills: {skills} valid\nCases: {cases} valid\nInstructors: {instructors} registered")
    raise SystemExit(0 if all(r.valid for r in reports) else 1)
if __name__=="__main__": main()
