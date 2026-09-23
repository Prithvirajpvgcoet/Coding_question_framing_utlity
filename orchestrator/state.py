"""
Question State Object (QSO) — single source of truth for all 7 agents.
Passed through the entire LangGraph workflow.
"""
from typing import TypedDict


class QuestionStateObject(TypedDict, total=False):

    # ── Identity ──────────────────────────────────────────────────────────────
    request_id:     str
    question_id:    str
    client_id:      str
    version:        int

    # ── Pipeline Control ──────────────────────────────────────────────────────
    status:               str    # PROCESSING | AWAITING_REVIEW | APPROVED | REJECTED | NEEDS_HUMAN_REVIEW
    current_agent:        str    # Last agent to write state (e.g. 'agent_c.code_gen')
    retry_counts:         dict   # {'agent_c': 2, 'agent_d': 1}
    internal_retry_count: int    # Agent C internal retry counter (max = MAX_INTERNAL_RETRIES)
    revision_count:       int    # Total Agent F revision cycles (max = MAX_REVISION_CYCLES)
    error_log:            list   # [{'agent': str, 'reason': str, 'timestamp': str}]

    # ── Agent A Outputs ───────────────────────────────────────────────────────
    requirements: dict
    # {
    #   topic, subtopic, difficulty, question_type,
    #   target_language, max_solve_time_minutes, raw_request
    # }

    curriculum: dict
    # {
    #   topic_id, learning_objectives[], prerequisites[],
    #   topic_alignment_score
    # }

    client_config: dict
    # {
    #   question_style, difficulty_bias,
    #   html_template_id, html_template,
    #   code_template_id, code_template
    # }

    blueprint: dict
    # {
    #   scenario, constraints[], expected_complexity{time, space},
    #   key_concepts[], style_notes
    # }

    # ── Agent B Output ────────────────────────────────────────────────────────
    references: list
    # [{reference_id, title, similarity_score, usage_note, excerpt}]

    # ── Deduplication (between B and C) ──────────────────────────────────────
    deduplication: dict
    # {max_cosine_similarity, matched_reference_id, lexical_overlap_score, verdict}
    # verdict: 'PASS' | 'FLAG' | 'REJECT'

    # ── Agent C Internal Outputs (all 7 sub-steps) ────────────────────────────
    question: dict
    # {title, description, examples[], constraints[], follow_up, raw_text}

    html: dict
    # {formatted_question, html_valid, validation_errors[], template_id}

    solution_architecture: dict
    # {approach, algorithm, data_structures[], time_complexity, space_complexity, edge_cases[], implementation_notes}

    code: dict
    # {solution, function_signature, language, imports[]}

    formatted_code: dict
    # {solution, formatter_used, logic_preserved}

    test_cases: list
    # [{id, type: VISIBLE|HIDDEN, input, expected_output, description, covers_edge}]

    execution: dict
    # {all_passed, results[{test_case_id, actual_output, passed, runtime_ms, memory_kb, error}], solution_correctness_score}

    # ── Agent D Output ────────────────────────────────────────────────────────
    quality: dict
    # {pass, scores{technical_correctness, problem_clarity, topic_alignment, difficulty_accuracy, originality}, failure_reasons[]}

    consistency: dict
    # {consistent, mismatches[{component, description, severity: LOW|MEDIUM|HIGH}]}

    # ── Agent G Output ────────────────────────────────────────────────────────
    final_qa: dict
    # {approved, aggregate_score, deterministic_checks{visible_count, hidden_count, html_valid, code_compiles}, approval_notes, rejection_reasons[]}

    # ── Feedback Loop (Agents E + F) ─────────────────────────────────────────
    feedback_analysis: dict
    # {classified_type, severity, affected_components[], re_entry_agent: 'agent_a'|'agent_c'|'agent_d', structured_instructions}

    # ── Audit ─────────────────────────────────────────────────────────────────
    agent_run_ids: list
    created_at:    str
    updated_at:    str