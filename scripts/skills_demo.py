import sys
from pathlib import Path
from pprint import pprint

# Ensure we can import the 'backend' package when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.skills_service import SkillsEngine  # noqa: E402

def main(cv_path: str, jd_path: str):
    cv = Path(cv_path).read_text(encoding="utf-8")
    jd = Path(jd_path).read_text(encoding="utf-8")
    eng = SkillsEngine()
    out = eng.payload(cv, jd)
    pprint(out)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts\\skills_demo.py data\\sample_cv.txt data\\sample_jd.txt")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])