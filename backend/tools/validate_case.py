import argparse
from pathlib import Path
from .validation import validate_case
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("path",type=Path); parser.add_argument("--project-root",type=Path,default=Path.cwd()); args=parser.parse_args()
    report=validate_case(args.path.resolve(),args.project_root.resolve()); print(report.render()); raise SystemExit(0 if report.valid else 1)
if __name__=="__main__": main()
