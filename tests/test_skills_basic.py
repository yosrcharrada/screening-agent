from backend.app.services.skills_service import SkillsEngine

def test_gap_map_basic():
    cv = "Built Python ETL and optimized SQL queries. Docker for deployment."
    jd = "We need Python and SQL. Docker is a plus."
    eng = SkillsEngine()
    out = eng.payload(cv, jd)
    # Structure check
    assert "gap_map" in out and "evidence" in out and "similarities" in out
    # Obvious tech skills should not be "missing"
    statuses = {g["skill"]: g["status"] for g in out["gap_map"]}
    for s in ["python", "sql"]:
        assert statuses.get(s) in {"present", "partial"}
