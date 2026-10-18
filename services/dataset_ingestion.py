"""
Dataset Ingestion Service: Parses and ingests JSON, CSV, Markdown, TXT, Word (.docx),
and PDF (.pdf) files into the reference_documents knowledge store for Agent B retrieval.
"""
import os
import re
import json
import csv
import io
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import ReferenceDocument

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed_references"


def extract_text_from_pdf(content_bytes: bytes) -> str:
    """Extract all text from PDF bytes using pypdf with graceful fallback."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                pages_text.append(t.strip())
        if pages_text:
            return "\n\n".join(pages_text)
    except Exception as e:
        print(f"[Dataset Ingestion] pypdf extraction notice: {e}")

    try:
        # Fallback text decoding in case of stream or plain text embedded
        return content_bytes.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def extract_text_from_docx(content_bytes: bytes) -> str:
    """Extract text from Word (.docx) bytes using python-docx with zipfile XML fallback."""
    # Method 1: python-docx library
    try:
        import docx
        doc = docx.Document(io.BytesIO(content_bytes))
        chunks = []
        for p in doc.paragraphs:
            if p.text and p.text.strip():
                chunks.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    chunks.append(" | ".join(cells))
        if chunks:
            return "\n\n".join(chunks)
    except Exception as e:
        print(f"[Dataset Ingestion] python-docx extraction notice: {e}")

    # Method 2: Fallback to standard library zipfile + xml.etree.ElementTree
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texts = [node.text for node in tree.findall(".//w:t", ns) if node.text]
            if texts:
                return " ".join(texts).strip()
    except Exception as e:
        print(f"[Dataset Ingestion] zipfile XML extraction notice: {e}")

    return ""


def classify_domain_and_topic(text: str) -> tuple[str, str, List[str]]:
    """
    Intelligently infer domain, primary topic, and tags from freeform scenario text
    based on enterprise domain keywords.
    """
    lower = text.lower()

    if any(k in lower for k in ("payment", "ledger", "fraud", "transaction", "arbitrage", "fx", "double-entry", "banking", "wallet", "stripe", "visa")):
        return (
            "FinTech & Banking",
            "Distributed Transactions & High-Frequency Systems",
            ["fintech", "payments", "ledger", "concurrency"],
        )
    elif any(k in lower for k in ("warehouse", "inventory", "checkout", "cart", "fulfillment", "shipment", "amr", "bin packing", "logistics", "supply chain")):
        return (
            "E-Commerce & Logistics",
            "Optimization & Inventory State Machines",
            ["ecommerce", "logistics", "inventory", "routing"],
        )
    elif any(k in lower for k in ("can-bus", "can_bus", "telemetry", "sensor", "firmware", "ecu", "automotive", "ring buffer", "dsp", "microcontroller", "embedded")):
        return (
            "Embedded & Automotive",
            "Telemetry Ring Buffers & Sensor Signal Processing",
            ["embedded", "automotive", "telemetry", "real-time"],
        )
    elif any(k in lower for k in ("lru", "cache", "graph", "trie", "bloom filter", "topological", "distributed", "lock", "deadlock", "raft", "paxos", "concurrency")):
        return (
            "Core Algorithms & Distributed Systems",
            "Data Structures & Concurrency",
            ["algorithms", "distributed", "data-structures"],
        )
    elif any(k in lower for k in ("hl7", "fhir", "dicom", "patient", "hospital", "ehr", "medical", "clinical")):
        return (
            "Healthcare & MedTech",
            "Medical Data Streams & Protocol Parsing",
            ["healthcare", "medtech", "hl7"],
        )
    else:
        return (
            "Enterprise Systems",
            "Software Architecture & Algorithms",
            ["enterprise", "system-design"],
        )


def parse_json_content(raw_text: str) -> List[Dict[str, Any]]:
    """Parse JSON array or single object into a list of reference item dictionaries."""
    data = json.loads(raw_text)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        return [data]
    return []


def parse_csv_content(raw_text: str) -> List[Dict[str, Any]]:
    """Parse CSV text into structured scenario dictionaries."""
    f = io.StringIO(raw_text)
    reader = csv.DictReader(f)
    items = []
    for row in reader:
        title = row.get("title") or row.get("Title") or row.get("name") or "Reference Problem"
        topic = row.get("topic") or row.get("Topic") or "General"
        subtopic = row.get("subtopic") or row.get("Subtopic") or ""
        difficulty = (row.get("difficulty") or row.get("Difficulty") or "MEDIUM").upper()
        domain = row.get("domain") or row.get("Domain") or ""
        scenario = row.get("scenario") or row.get("description") or row.get("Scenario") or ""
        tags_raw = row.get("tags") or row.get("Tags") or ""
        tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]

        if not domain or not tags:
            inferred_domain, _, inferred_tags = classify_domain_and_topic(f"{title} {scenario}")
            domain = domain or inferred_domain
            tags = tags or inferred_tags

        items.append({
            "title": title,
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "domain": domain,
            "scenario": scenario,
            "tags": tags,
            "algorithmic_pattern": row.get("algorithmic_pattern", ""),
        })
    return items


def parse_unstructured_document(raw_text: str, filename: str) -> List[Dict[str, Any]]:
    """
    Parse freeform or structured text from Word (.docx), PDF (.pdf), Markdown (.md),
    or plain text (.txt). Automatically detects:
    - Multi-problem sections (e.g. Problem 1:, Scenario 2:, --- dividers)
    - Metadata tags (Title:, Topic:, Subtopic:, Difficulty:, Domain:, Tags:)
    - Automatic keyword-based classification fallback.
    """
    clean_base_title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
    text = raw_text.strip()
    if not text:
        return []

    # Detect if document has multiple distinct sections
    # Split by: "Problem X:", "Scenario X:", "Question X:", "Case Study X:", or markdown "---"
    split_pattern = r"(?im)(?=(?:^|\n)(?:###?\s*)?(?:problem|scenario|question|case study)\s*[\d#A-Z]+[:\.\-])|(?:\n---+\n)"
    raw_sections = [s.strip() for s in re.split(split_pattern, text) if s and len(s.strip()) > 30]

    # If splitting resulted in no discrete sections, treat whole document as one
    if not raw_sections:
        raw_sections = [text]

    items: List[Dict[str, Any]] = []

    for idx, sec in enumerate(raw_sections):
        # Extract explicit metadata headers if author supplied them
        m_title = re.search(r"(?im)^title:\s*([^\n]+)", sec)
        m_topic = re.search(r"(?im)^topic:\s*([^\n]+)", sec)
        m_subtopic = re.search(r"(?im)^subtopic:\s*([^\n]+)", sec)
        m_diff = re.search(r"(?im)^difficulty:\s*(EASY|MEDIUM|HARD|EXPERT)", sec)
        m_domain = re.search(r"(?im)^domain:\s*([^\n]+)", sec)
        m_tags = re.search(r"(?im)^tags:\s*([^\n]+)", sec)

        inferred_domain, inferred_topic, inferred_tags = classify_domain_and_topic(sec)

        # Title resolution
        if m_title:
            title = m_title.group(1).strip()
        else:
            first_line = sec.splitlines()[0].strip().lstrip("#").strip()
            # If multi-section document, append section number if title is generic
            if len(first_line) > 5 and len(first_line) <= 80:
                title = first_line
            elif len(raw_sections) > 1:
                title = f"{clean_base_title} - Scenario {idx + 1}"
            else:
                title = clean_base_title

        # Topic & Subtopic resolution
        topic = m_topic.group(1).strip() if m_topic else inferred_topic
        subtopic = m_subtopic.group(1).strip() if m_subtopic else ""

        # Difficulty resolution
        difficulty = m_diff.group(1).upper() if m_diff else "MEDIUM"

        # Domain resolution
        domain = m_domain.group(1).strip() if m_domain else inferred_domain

        # Tags resolution
        if m_tags:
            tags = [t.strip().lower() for t in m_tags.group(1).split(",") if t.strip()]
        else:
            tags = inferred_tags

        items.append({
            "title": title,
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "domain": domain,
            "scenario": sec,
            "tags": tags,
            "algorithmic_pattern": "",
        })

    return items


def parse_text_or_markdown(raw_text: str, filename: str) -> List[Dict[str, Any]]:
    """Legacy helper: alias for parse_unstructured_document."""
    return parse_unstructured_document(raw_text, filename)


def parse_uploaded_dataset(filename: str, content_bytes: bytes, default_doc_type: str = "reference_question") -> List[Dict[str, Any]]:
    """
    Main entry point: parses raw file bytes (PDF, Word DOCX, JSON, CSV, MD, TXT)
    into a list of normalized scenario items.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(content_bytes)
        items = parse_unstructured_document(raw_text, filename)
    elif ext in (".docx", ".doc"):
        raw_text = extract_text_from_docx(content_bytes)
        items = parse_unstructured_document(raw_text, filename)
    elif ext in (".json", ".jsonl"):
        raw_text = content_bytes.decode("utf-8", errors="replace")
        items = parse_json_content(raw_text)
    elif ext in (".csv", ".tsv"):
        raw_text = content_bytes.decode("utf-8", errors="replace")
        items = parse_csv_content(raw_text)
    else:
        # Markdown (.md) or Plain Text (.txt)
        raw_text = content_bytes.decode("utf-8", errors="replace")
        items = parse_unstructured_document(raw_text, filename)

    for it in items:
        if "doc_type" not in it:
            it["doc_type"] = default_doc_type
    return items


async def ingest_file_content(
    db: Optional[AsyncSession],
    client_id: str,
    filename: str,
    content_bytes: bytes,
    doc_type: str = "DOMAIN_SCENARIO",
    extra_tags: Optional[List[str]] = None,
) -> List[dict]:
    """
    Ingest a file (PDF, Word, JSON, CSV, MD, or TXT) and persist reference documents
    to the database (or return in-memory records if DB is not provided).
    """
    try:
        c_uuid = uuid.UUID(client_id)
    except ValueError:
        c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    ext = Path(filename).suffix.lower()
    file_format = "txt"
    if ext == ".pdf":
        file_format = "pdf"
    elif ext in (".docx", ".doc"):
        file_format = "docx"
    elif ext in (".json", ".jsonl"):
        file_format = "json"
    elif ext in (".csv", ".tsv"):
        file_format = "csv"
    elif ext in (".md", ".markdown"):
        file_format = "md"
    else:
        file_format = "txt"

    parsed_items = parse_uploaded_dataset(filename, content_bytes, default_doc_type=doc_type)

    now = datetime.datetime.now(datetime.UTC)
    saved_records = []

    for item in parsed_items:
        tags = list(item.get("tags", []))
        if extra_tags:
            tags.extend(extra_tags)
        # Deduplicate tags
        tags = list(dict.fromkeys(tags))

        doc = ReferenceDocument(
            id=uuid.uuid4(),
            client_id=c_uuid,
            title=item.get("title", "Reference Scenario"),
            doc_type=doc_type,
            format=file_format,
            topic=item.get("topic", "General"),
            subtopic=item.get("subtopic", ""),
            difficulty=item.get("difficulty", "MEDIUM"),
            domain=item.get("domain", ""),
            tags=tags,
            raw_content=item.get("scenario", "") or json.dumps(item),
            structured_data=item,
            created_at=now,
        )

        if db is not None:
            db.add(doc)

        saved_records.append({
            "id": str(doc.id),
            "title": doc.title,
            "topic": doc.topic,
            "subtopic": doc.subtopic,
            "difficulty": doc.difficulty,
            "domain": doc.domain,
            "tags": doc.tags,
            "format": doc.format,
        })

    if db is not None:
        await db.commit()

    return saved_records


async def load_seed_datasets(db: Optional[AsyncSession] = None, client_id: str = "00000000-0000-0000-0000-000000000001") -> List[dict]:
    """
    Reads the local seed JSON files from data/seed_references/ and loads them.
    If db session is passed, commits to the database; otherwise returns parsed dicts.
    """
    all_seeds = []
    if not SEED_DIR.exists():
        return all_seeds

    for json_file in SEED_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                if isinstance(items, list):
                    all_seeds.extend(items)
        except Exception as e:
            print(f"[Dataset Ingestion] Warning reading {json_file.name}: {e}")

    if db is not None and all_seeds:
        try:
            c_uuid = uuid.UUID(client_id)
        except ValueError:
            c_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

        now = datetime.datetime.now(datetime.UTC)
        for item in all_seeds:
            # Check if title already exists to prevent duplicate seeding
            res = await db.execute(
                select(ReferenceDocument).where(
                    ReferenceDocument.client_id == c_uuid,
                    ReferenceDocument.title == item.get("title")
                )
            )
            existing = res.scalar_one_or_none()
            if existing is None:
                doc = ReferenceDocument(
                    id=uuid.uuid4(),
                    client_id=c_uuid,
                    title=item.get("title", "Reference Scenario"),
                    doc_type="DOMAIN_SCENARIO",
                    format="json",
                    topic=item.get("topic", "General"),
                    subtopic=item.get("subtopic", ""),
                    difficulty=item.get("difficulty", "MEDIUM"),
                    domain=item.get("domain", ""),
                    tags=item.get("tags", []),
                    raw_content=item.get("scenario", "") or json.dumps(item),
                    structured_data=item,
                    created_at=now,
                )
                db.add(doc)
        await db.commit()

    return all_seeds
