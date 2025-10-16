from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import csv
import yaml

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
CONFIG = ROOT / "config"

class QuestionBank:
    def __init__(self, csv_path: Path = DATA / "questions.csv", thresholds_path: Path = CONFIG / "thresholds.yaml"):
        # Use utf-8-sig so a BOM in the CSV header doesn't break DictReader keys
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            self.rows = [row for row in r]
        # Use utf-8-sig to strip BOM in YAML too
        with open(thresholds_path, "r", encoding="utf-8-sig") as f:
            cfg = yaml.safe_load(f)
        self.max_q = int(cfg.get("max_questions", 5))

    def generate(self, gap_map: List[Dict]) -> List[Dict]:
        missing = [g["skill"] for g in gap_map if g["status"] == "missing"]
        partial = [g["skill"] for g in gap_map if g["status"] == "partial"]
        targets = (missing + partial)[:3] or ["generic"]

        picked: List[Dict] = []
        used_ids = set()

        # Skill-specific first
        for skill in targets:
            for row in self.rows:
                if row.get("skill_tag", "").lower() == skill.lower() and row.get("id") not in used_ids:
                    picked.append({
                        "id": row["id"],
                        "text": row["text"].replace("{skill}", skill),
                        "difficulty": row["difficulty"],
                        "rationale": f"Targets gap: {skill}"
                    })
                    used_ids.add(row["id"])
                    if len(picked) >= self.max_q:
                        return picked

        # Generic templates using the top target
        main = targets[0]
        for row in self.rows:
            if row.get("skill_tag", "").lower() == "generic" and row.get("id") not in used_ids:
                picked.append({
                    "id": row["id"],
                    "text": row["text"].replace("{skill}", main),
                    "difficulty": row["difficulty"],
                    "rationale": f"Targets gap: {main}"
                })
                used_ids.add(row["id"])
                if len(picked) >= self.max_q:
                    break

        return picked