import json
from pathlib import Path


def test_engineering_backlog_has_consistent_task_records() -> None:
    backlog_path = (
        Path(__file__).resolve().parents[1] / "docs" / "engineering-backlog" / "tasks.json"
    )
    tasks = json.loads(backlog_path.read_text(encoding="utf-8"))
    required = {
        "task_id",
        "title",
        "category",
        "difficulty",
        "affected_modules",
        "type",
        "problem_statement",
        "expected_behavior",
        "acceptance_criteria",
        "potential_edge_cases",
        "testing_requirements",
        "relevant_files",
        "dependencies",
    }
    allowed_types = {
        "verified_bug",
        "proposed_feature",
        "technical_debt",
        "future_improvement",
        "research",
    }
    task_ids = [task["task_id"] for task in tasks]

    assert len(tasks) == 90
    assert len(task_ids) == len(set(task_ids))
    for task in tasks:
        assert required <= task.keys()
        assert set(task) <= required | {
            "current_behavior",
            "reproduction_steps",
            "implementation_notes",
        }
        assert task["type"] in allowed_types
        assert set(task["dependencies"]) <= set(task_ids)
