import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage import Store
from workflow import step, fork_one


def fake_api():
    calls = []
    def call(prompt, *, previous_response_id=None):
        rid = f"resp-{len(calls)+1}"
        calls.append((rid, previous_response_id, prompt))
        return {"id": rid, "parent_id": previous_response_id,
                "prompt": prompt, "text": f"answer {rid}", "status": "completed"}
    return call, calls


def test_fork_lineage_and_restart(tmp_path):
    db = Store(str(tmp_path / "runs.db"))
    run = db.new()
    call, calls = fake_api()
    step(run, "base", call); db.save(run)
    fork_one(run, "bull", call); db.save(run)
    fork_one(run, "bear", call); db.save(run)
    assert run["bull"][0]["parent_id"] == run["base"]["id"]
    assert run["bear"][0]["parent_id"] == run["base"]["id"]
    assert run["bull"][0]["id"] != run["bear"][0]["id"]
    step(run, "continue", call, branch="bull"); db.save(run)
    assert run["bull"][-1]["parent_id"] == run["bull"][0]["id"]
    assert run["bull"][-1]["parent_id"] != run["bear"][0]["id"]
    restored = Store(str(tmp_path / "runs.db")).load(run["id"])
    step(restored, "resume", call, branch="bull")
    assert restored["bull"][-1]["parent_id"] == run["bull"][-1]["id"]
    step(restored, "compare", call)
    assert restored["comparison"]["parent_id"] is None
    assert "answer" in restored["comparison"]["prompt"]
    assert len(calls) == 6
