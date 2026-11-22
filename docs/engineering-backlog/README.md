# Engineering Backlog

The backlog contains 90 structured, implementation-suitable tasks. Each task has an objective,
category, difficulty, affected modules, problem statement, acceptance criteria, edge cases,
testing requirements, likely files, dependencies, and type.

Task types distinguish `verified_bug`, `proposed_feature`, `technical_debt`,
`future_improvement`, and `research`. Only reproducible defects confirmed in the current code are
marked `verified_bug`; enhancement proposals and unverified risks use other types.

`verified_bug` is reserved for defects with an executable reproduction or regression test in the
repository. Do not treat the presence of a task entry as evidence that its defect exists. The
current backlog uses enhancement, debt, improvement, and research types where the issue is not
reproduced as a defect.

Every entry uses the same keys. `current_behavior` and `reproduction_steps` are optional for
proposals; `implementation_notes` is optional. Task IDs are unique, dependencies refer to other
task IDs, and task type is independent from category.

See [tasks.json](tasks.json).
