"""
Reference Retriever Service: 3-Stage Hybrid RAG Retriever for Agent B.

Stage 1: Exact doc_type=AUTHORING_SPEC retrieval → returns formatting rules + HTML template + code stubs.
Stage 2: Keyword-scored domain scenario retrieval → returns top-N relevant problem scenarios.
Stage 3: Assemble RAG bundle → {authoring_spec, domain_references} returned to Agent C.
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ReferenceDocument
from services.dataset_ingestion import load_seed_datasets


def _score_item(item: Dict[str, Any], topic: str, subtopic: str, difficulty: str, category: str = "") -> int:
    """Computes relevance score between a seed item and the requirements."""
    score = 0
    item_topic     = str(item.get("topic", "")).lower()
    item_subtopic  = str(item.get("subtopic", "")).lower()
    item_diff      = str(item.get("difficulty", "")).upper()
    item_tags      = [str(t).lower() for t in item.get("tags", [])]
    item_category  = str(item.get("category", "")).lower()

    req_topic      = topic.lower()
    req_subtopic   = subtopic.lower()
    req_diff       = difficulty.upper()
    req_category   = category.lower() if category else ""

    # Category match (strongest signal)
    if req_category and item_category and (req_category in item_category or item_category in req_category):
        score += 15

    # Topic match
    if req_topic and (req_topic in item_topic or item_topic in req_topic):
        score += 10
    elif any(req_topic in t for t in item_tags):
        score += 8

    # Subtopic match
    if req_subtopic:
        if req_subtopic in item_subtopic or item_subtopic in req_subtopic:
            score += 6
        elif any(req_subtopic in t for t in item_tags):
            score += 5

    # Difficulty match
    if req_diff and req_diff == item_diff:
        score += 3

    return score


def _extract_authoring_spec(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the structured authoring spec fields from a seed item or DB record's structured_data.
    Returns: {html_template, standard_format_rules, starter_code_snippets, test_cases, ...}
    """
    sd = item.get("structured_data", {}) or {}

    # Direct top-level keys take priority over nested structured_data
    spec = {
        "html_template":          item.get("html_template")          or sd.get("html_template", ""),
        "standard_format_rules":  item.get("standard_format_rules")  or sd.get("standard_format_rules", {}),
        "starter_code_snippets":  item.get("starter_code_snippets")  or sd.get("starter_code_snippets") or sd.get("starter_code_templates", {}),
        "test_cases":             item.get("test_cases")             or sd.get("test_cases")            or sd.get("test_cases_table", []),
        "solution_code":          item.get("solution_code")          or sd.get("solution_code", {}),
        "scenario":               item.get("scenario")               or sd.get("scenario", ""),
        "title":                  item.get("title")                  or sd.get("title", ""),
        "category":               item.get("category")               or sd.get("category", "DSA"),
        "retrieval_summary":      item.get("retrieval_summary")      or sd.get("retrieval_summary", ""),
        "function_description":   item.get("function_description")   or sd.get("function_description", ""),
        "input_format":           item.get("input_format")           or sd.get("input_format", ""),
        "output_format":          item.get("output_format")          or sd.get("output_format", ""),
        "sample_input":           item.get("sample_input")           or sd.get("sample_input", ""),
        "sample_output":          item.get("sample_output")          or sd.get("sample_output", ""),
        "explanation":            item.get("explanation")            or sd.get("explanation", ""),
        "constraints":            item.get("constraints")            or sd.get("constraints", []),
    }
    return spec


async def retrieve_references(
    requirements: Dict[str, Any],
    client_id: str,
    limit: int = 3,
    db: Optional[AsyncSession] = None,
) -> List[Dict[str, Any]]:
    """
    3-Stage Hybrid RAG Retriever.

    Returns a list where the FIRST item is always the AUTHORING_SPEC (formatting rules + code stubs),
    and the remaining items are domain scenario references.

    Downstream (Agent C) should check item["doc_type"] == "AUTHORING_SPEC" to separate them.
    """
    topic      = requirements.get("topic", "")
    subtopic   = requirements.get("subtopic", "")
    difficulty = requirements.get("difficulty", "MEDIUM")
    category   = requirements.get("category", "DSA")

    authoring_spec = None
    domain_scenarios: List[Dict[str, Any]] = []

    # ──────────────────────────────────────────────────
    # STAGE 1: Try DB for AUTHORING_SPEC
    # ──────────────────────────────────────────────────
    if db is not None:
        try:
            c_uuid = uuid.UUID(client_id)
        except ValueError:
            c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

        try:
            # Fetch authoring spec
            spec_stmt = (
                select(ReferenceDocument)
                .where(
                    ReferenceDocument.client_id == c_uuid,
                    ReferenceDocument.doc_type == "AUTHORING_SPEC",
                )
                .limit(1)
            )
            spec_res = await db.execute(spec_stmt)
            spec_doc = spec_res.scalars().first()

            if spec_doc:
                sd = spec_doc.structured_data or {}
                extracted = _extract_authoring_spec({"title": spec_doc.title, "scenario": spec_doc.raw_content, "structured_data": sd})
                authoring_spec = {
                    "doc_type": "AUTHORING_SPEC",
                    "id": str(spec_doc.id),
                    **extracted
                }

            # Fetch domain scenarios
            scenario_stmt = (
                select(ReferenceDocument)
                .where(
                    ReferenceDocument.client_id == c_uuid,
                    ReferenceDocument.doc_type != "AUTHORING_SPEC",
                    or_(
                        func.lower(ReferenceDocument.topic) == topic.lower(),
                        func.lower(ReferenceDocument.subtopic) == subtopic.lower(),
                        ReferenceDocument.tags.contains([topic.lower()]),
                    )
                )
                .limit(limit * 2)
            )
            scenario_res = await db.execute(scenario_stmt)
            scenario_docs = scenario_res.scalars().all()

            for doc in scenario_docs:
                data = doc.structured_data or {}
                domain_scenarios.append({
                    "doc_type": "DOMAIN_SCENARIO",
                    "id": str(doc.id),
                    "title": doc.title,
                    "domain": doc.domain or data.get("domain", "Enterprise Domain"),
                    "topic": doc.topic,
                    "subtopic": doc.subtopic,
                    "difficulty": doc.difficulty,
                    "scenario": doc.raw_content or data.get("scenario", ""),
                    "algorithmic_pattern": data.get("algorithmic_pattern", ""),
                    "sample_constraints": data.get("sample_constraints", []),
                })
        except Exception as e:
            print(f"[Reference Retriever] DB query notice: {e}")

    # ──────────────────────────────────────────────────
    # STAGE 2: Fallback to seed datasets
    # ──────────────────────────────────────────────────
    seed_items = await load_seed_datasets()

    if authoring_spec is None:
        # Find AUTHORING_SPEC from seeds matching category if possible
        matched_specs = []
        for item in seed_items:
            if item.get("doc_type") == "AUTHORING_SPEC" or item.get("structured_data", {}).get("doc_type") == "AUTHORING_SPEC":
                item_cat = str(item.get("category") or item.get("structured_data", {}).get("category", "")).lower()
                extracted = _extract_authoring_spec(item)
                spec_dict = {
                    "doc_type": "AUTHORING_SPEC",
                    **extracted
                }
                if category and category.lower() in item_cat:
                    matched_specs.insert(0, spec_dict)
                else:
                    matched_specs.append(spec_dict)

        if matched_specs:
            authoring_spec = matched_specs[0]
            print(f"[Agent B Stage 1] Found AUTHORING_SPEC from seeds: {authoring_spec.get('title')} (category: {authoring_spec.get('category')})")

    if len(domain_scenarios) < limit:
        # Score and rank seed items for domain scenarios
        scored_seeds = []
        existing_titles = {s.get("title") for s in domain_scenarios}
        for item in seed_items:
            item_dt = item.get("doc_type") or item.get("structured_data", {}).get("doc_type", "")
            if item_dt == "AUTHORING_SPEC":
                continue  # Skip spec items for domain refs
            if item.get("title") in existing_titles:
                continue
            s = _score_item(item, topic, subtopic, difficulty, category)
            scored_seeds.append((s, item))

        scored_seeds.sort(key=lambda x: x[0], reverse=True)
        needed = limit - len(domain_scenarios)
        for _, seed in scored_seeds[:needed]:
            domain_scenarios.append({
                "doc_type": "DOMAIN_SCENARIO",
                "title": seed.get("title"),
                "domain": seed.get("domain", "General Enterprise"),
                "topic": seed.get("topic"),
                "subtopic": seed.get("subtopic"),
                "difficulty": seed.get("difficulty"),
                "scenario": seed.get("scenario"),
                "algorithmic_pattern": seed.get("algorithmic_pattern"),
                "sample_constraints": seed.get("sample_constraints", []),
                "structured_data": seed.get("structured_data", {}),
            })

    # ──────────────────────────────────────────────────
    # STAGE 3: Assemble RAG bundle
    # ──────────────────────────────────────────────────
    result: List[Dict[str, Any]] = []
    if authoring_spec:
        result.append(authoring_spec)
        print(f"[Agent B Stage 3] AUTHORING_SPEC loaded: {authoring_spec.get('title', 'unknown')}")
    else:
        print("[Agent B Stage 3] WARNING: No AUTHORING_SPEC found — Agent C will use fallback HTML builder")

    result.extend(domain_scenarios[:limit])
    print(f"[Agent B Stage 3] Returning {len(result)} references (1 spec + {len(domain_scenarios[:limit])} scenarios)")
    return result
