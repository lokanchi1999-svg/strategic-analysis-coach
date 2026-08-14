import argparse
from pathlib import Path
from .validation import validate_skill
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("path",type=Path); args=parser.parse_args()
    report=validate_skill(args.path.resolve()); print(report.render()); raise SystemExit(0 if report.valid else 1)
if __name__=="__main__": main()
