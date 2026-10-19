# Agent E feedback pipeline assessment

## Scope and test setup

This assessment traces `agents/agent_e/runner.py` and the feedback path it hands
off to Agent F. The offline test uses:

- `tests/fixtures/agent_e_feedback.json` as dummy rejected-question feedback.
- `tests/fixtures/agent_e_formatted_response.json` as the dummy JSON response
  from the classifier.
- A mocked `groq_chat` and audit logger, so it needs neither a Groq API key nor
  a database or Redis service.
- The existing `.venv` uses Python 3.14.3; `pytest` and `pytest-asyncio` from
  the project's declared development dependencies were installed there for
  repeatable local runs.

Run the test from the repository root with:

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\test_agent_e_runner.py -q
```

It verifies feedback extraction, prompt use, fenced JSON parsing, audit-log
dispatch, all three Agent F category routes, and the route function used by
the feedback worker. It does not call the external model or execute the
database-backed Celery task.

## What works

- The runner calls the cheaper model with low temperature and JSON response
  mode for classification.
- Markdown JSON fences are removed before parsing.
- A valid `FORMATTING` classification is handed to Agent F and resolves to
  `agent_d`; corresponding categories route to `agent_a` or `agent_c`.
- The classification prompt exists at `prompts/agent_e_feedback.txt`.

## Findings

| Priority | Finding | Impact | Simplest reliable correction |
|---|---|---|---|
| High | `json.loads` failures are caught broadly and converted into a fabricated `HIGH`/`LOGIC` classification, but the run is still logged as `SUCCESS` (`agents/agent_e/runner.py`, parse/fallback and log sections). | Invalid model output silently sends a logic/code revision to Agent C and creates misleading audit data. | Catch `json.JSONDecodeError` specifically and return/raise an explicit classification failure; log a failure status instead of success. |
| High | Parsed JSON is not validated for object type, required keys, or allowed enum values. | A JSON object with a missing/unknown category can route to Agent C by default; a non-object JSON value instead raises an unhandled attribute error when `.get` is called. | Validate the parsed object against the prompt's small schema (`severity`, `category`, `summary`) before updating state. |
| High | The worker calculates `target = route_after_agent_f(state)` but then calls `workflow.ainvoke(state)` without using `target`; the compiled graph's entry point is `agent_a` (`workers/tasks.py`, `_feedback_revision`; `orchestrator/graph.py`, `build_graph`). | Every feedback revision restarts generation from Agent A rather than re-entering at the classifier-selected agent. | Make the graph entry node configurable for the feedback invocation, or create a focused feedback graph that starts at the selected re-entry node. Test each category through that invocation. |
| Medium | Prompt loading is relative to the current working directory and `load_prompt` silently substitutes a TODO prompt on a missing file (`agents/base.py`, `load_prompt`). | A worker started from a different directory can make a real model call with a placeholder instruction. | Resolve prompt files relative to the package/repository location and fail fast when a required prompt is missing. |
| Medium | Audit logging is scheduled with `asyncio.ensure_future` and not awaited (`agents/agent_e/runner.py`). Celery runs this path inside `asyncio.run`, which closes the loop when the task returns. | The audit write can be cancelled during task shutdown, losing usage/run metadata. | Await `log_agent_run` directly (the helper already catches persistence failures), or use a managed background-task mechanism whose lifetime is guaranteed. |
| Low | The runner uses a dynamic `__import__` for a known logger module and uses `print` for operational messages. | This adds indirection and makes logging less structured/testable. | Import `log_agent_run` normally and use the existing application logger. |

## Recommended order

1. Fix the worker's ignored `target`; otherwise the category routing result has
   no effect on the full revision workflow.
2. Validate classifier output and make malformed output an explicit failure.
3. Make prompt lookup deterministic and required.
4. Await audit logging, then replace prints/dynamic imports as a small cleanup.

The focused offline test passes through Agent E and Agent F without external
services. The worker's database/Celery portion and the graph re-entry defect
remain outside that mocked test and need a separate worker-level regression
test when the workflow entry-point behavior is changed.
