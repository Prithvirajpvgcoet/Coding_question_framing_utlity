# Full pipeline assessment

## Reproduction

The offline path uses `.env.example`, `tests/fixtures/offline_pipeline_input.json`,
`tests/fixtures/offline_reference_data.json`, and
`tests/fixtures/dummy_solution_unformatted.py`. It does not require Postgres,
Redis, Groq, Judge0, or Langfuse. Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\integration\test_offline_full_pipeline.py -q
```

The test stubs only external model, persistence, retrieval, and sandbox calls;
it executes the real LangGraph topology and real formatter.

## Findings

| Priority | Evidence | Impact | Simplest fix |
|---|---|---|---|
| Critical | `orchestrator/edges.py::route_after_dedup` returned `agent_d` for PASS/FLAG, but `orchestrator/graph.py` did not map `agent_d`; the offline test reproduced `KeyError: 'agent_d'`. The graph also placed dedup before Agent C. | The normal path either crashed or evaluated an empty question. | Dedup after Agent C and map PASS/FLAG to Agent D. This is fixed in this patch. |
| Critical | `workers/tasks.py` computes `target = route_after_agent_f(state)` and then calls `workflow.ainvoke(state)`; `orchestrator/graph.py` always starts at `agent_a`. | Feedback revisions ignore Agent F's selected re-entry route and regenerate from the beginning. | Add a `build_graph(entry_point=...)` option or dedicated feedback graph, then invoke it with `target`. |
| High | `agents/agent_c/runner.py` returned `generated_question`, `solution_code`, and `sandbox_passed`, which are not declared in `QuestionStateObject`; LangGraph drops undeclared state keys. | Downstream agents received empty/default values and could approve incomplete output. | Emit declared `question`, `code`, `execution`, and `html` fields. This is fixed in this patch; remove legacy aliases after migration. |
| High | Agent E catches every parse error and fabricates a `HIGH`/`LOGIC` classification; Agent D similarly turns malformed scoring into a low score. | Invalid model output becomes a misleading route or an opaque retry instead of a diagnosable failure. | Validate JSON with Pydantic/jsonschema and mark the agent run failed on invalid output. |
| High | Agent A and D use `asyncio.ensure_future` for audit writes, while Celery wraps the task in `asyncio.run`. | Audit tasks can be cancelled when the event loop closes. | Await `log_agent_run` directly; keep persistence failures non-fatal inside the logger. |
| Medium | `agents/base.py` resolves prompts relative to the current working directory and substitutes a TODO prompt when missing. | Starting API/worker from another directory can send a placeholder system prompt. | Resolve from `Path(__file__)` and raise a startup/configuration error when a prompt is absent. |
| Medium | `agents/agent_b/runner.py` deduplicated `state["question"]`, but Agent C wrote `generated_question`; the graph also placed dedup before Agent C. | Deduplication saw empty text and could not protect generated questions. | Move dedup after Agent C and normalize the question key. Both are fixed in this patch. |
| Medium | `QUALITY_PASS_THRESHOLD` is interpreted as `4.0` by Agent D but as `70` by Agent G; the checked-in `.env` defines it twice. | Quality decisions are inconsistent across agents and depend on duplicate env ordering. | Use separate names (`QUALITY_SCORE_THRESHOLD`, `FINAL_QA_PERCENT_THRESHOLD`) or one normalized 0–1/0–100 scale. |
| Low | ORM JSON columns use mutable literal defaults such as `default={}` and `default=[]`. | Shared mutable defaults are unsafe and obscure state ownership. | Use `default=dict` and `default=list`. |
| Low | API persistence catches `Exception` and continues enqueueing; feedback uses dynamic imports and silently skips missing models. | Requests can return success while database state was not saved. | Log the exception and return a clear dependency failure; use direct imports. |
| Medium | The full suite has DOCX/PDF failures because `pypdf` and `python-docx` are used by ingestion but were missing from `pyproject.toml`/the environment. | Supported upload formats fail or silently fall back to raw bytes. | Declare both runtime dependencies. They are added in this patch. |
| Medium | Three existing `*_live` tests call Groq unconditionally, and two sandbox tests require Windows subprocess pipe permissions. | CI/local runs are not deterministic and cannot be completed offline in restricted environments. | Mark live tests with an explicit opt-in marker/env guard; run sandbox tests in a worker/container with subprocess permissions. |

## Recommended implementation order

1. Normalize the QSO keys and add schema validation at every agent boundary.
2. Fix graph re-entry and move/repair deduplication; add route-specific tests.
3. Await audit writes and make prompt resolution deterministic.
4. Remove duplicate threshold settings and align units.
5. Replace broad exception swallowing and mutable ORM defaults.

The smallest safe first release is steps 1–3: they fix correctness, make
failures observable, and avoid introducing new infrastructure.

## Validation result

The new offline integration test passes. The full existing suite reached 37
passed and 12 failed: live API/network tests, missing parser dependencies (now
declared), PDF fallback behavior, and Windows subprocess permission failures.
