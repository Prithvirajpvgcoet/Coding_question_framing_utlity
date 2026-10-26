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


def _clean_utf8(text: str) -> str:
    """Strip NUL (0x00) and other invalid characters for PostgreSQL text and jsonb fields."""
    if not text:
        return ""
    # PostgreSQL cannot store NUL (0x00) bytes in VARCHAR / TEXT / JSONB
    return text.replace("\x00", "").replace("\u0000", "")


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
            return _clean_utf8("\n\n".join(pages_text))
    except Exception as e:
        print(f"[Dataset Ingestion] pypdf extraction notice: {e}")

    try:
        # Avoid decoding binary compressed streams directly into database text
        decoded = content_bytes.decode("utf-8", errors="ignore").strip()
        # If binary stream markers dominate, return only printable text segments
        printable = "".join(c for c in decoded if c.isprintable() or c in ("\n", "\r", "\t"))
        return _clean_utf8(printable)
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
            return _clean_utf8("\n\n".join(chunks))
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
                return _clean_utf8(" ".join(texts).strip())
    except Exception as e:
        print(f"[Dataset Ingestion] zipfile XML extraction notice: {e}")

    return ""


def classify_domain_and_topic(text: str) -> tuple[str, str, List[str]]:
    """
    Intelligently infer domain, primary topic, and tags from freeform scenario text
    based on enterprise domain keywords.
    """
    lower = text.lower()

    if any(k in lower for k in ("fintech", "banking", "payment", "ledger", "transaction", "reconciliation", "settlement", "fraud", "card", "iban", "swift", "iso20022")):
        return (
            "FinTech & Banking",
            "Distributed Transactions & High-Frequency Systems",
            ["fintech", "payments", "ledger", "concurrency"],
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
    elif any(k in lower for k in ("game", "physics", "rendering", "graphics", "shader", "collision", "vulkan", "opengl")):
        return (
            "Gaming & Graphics",
            "Game Mechanics & Physics Math",
            ["gaming", "graphics", "physics"],
        )
    else:
        return (
            "General Algorithms",
            "Data Structures & Problem Solving",
            ["algorithms", "general"],
        )


def parse_json_content(raw_text: str) -> List[Dict[str, Any]]:
    """Parse JSON array or single object into a list of reference item dictionaries."""
    data = json.loads(_clean_utf8(raw_text))
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        return [data]
    return []


def parse_csv_content(raw_text: str) -> List[Dict[str, Any]]:
    """Parse CSV text into structured scenario dictionaries."""
    f = io.StringIO(_clean_utf8(raw_text))
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
    text = _clean_utf8(raw_text.strip())
    if not text:
        return []

    # Detect if document has multiple distinct sections
    # Split by: "Problem X:", "Scenario X:", "Question X:", "Case Study X:", or markdown "---"
    split_pattern = r"(?im)(?=(?:^|\n)(?:###?\s*)?(?:problem|scenario|question|case study)\s*[\d#A-Z]+[:\.\-])|(?:\n---+\n)"
    raw_sections = [s.strip() for s in re.split(split_pattern, text) if s and len(s.strip()) > 30]

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
            # If title extracted begins with PDF or binary markers, use filename
            if first_line.startswith("%PDF") or len(first_line) > 80 or len(first_line) < 3:
                title = clean_base_title if len(raw_sections) == 1 else f"{clean_base_title} - Scenario {idx + 1}"
            else:
                title = first_line

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
        raw_text = _clean_utf8(content_bytes.decode("utf-8", errors="replace"))
        items = parse_json_content(raw_text)
    elif ext in (".csv", ".tsv"):
        raw_text = _clean_utf8(content_bytes.decode("utf-8", errors="replace"))
        items = parse_csv_content(raw_text)
    else:
        # Markdown (.md) or Plain Text (.txt)
        raw_text = _clean_utf8(content_bytes.decode("utf-8", errors="replace"))
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
    custom_topic: Optional[str] = None,
    custom_domain: Optional[str] = None,
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

    now = datetime.datetime.now(datetime.timezone.utc)
    saved_records = []

    for item in parsed_items:
        tags = list(item.get("tags", []))
        if extra_tags:
            tags.extend(extra_tags)
        # Deduplicate tags
        tags = list(dict.fromkeys(tags))

        final_topic = custom_topic.strip() if custom_topic and custom_topic.strip() else item.get("topic", "General")
        final_domain = custom_domain.strip() if custom_domain and custom_domain.strip() else item.get("domain", "General Algorithms")
        
        # Clean string attributes to guarantee no NUL bytes (0x00) reach Postgres UTF-8 columns
        clean_title = _clean_utf8(item.get("title", "Reference Scenario"))
        clean_scenario = _clean_utf8(item.get("scenario", "") or json.dumps(item))

        # Deep clean structured_data dictionary
        clean_item = json.loads(_clean_utf8(json.dumps(item)))

        doc = ReferenceDocument(
            id=uuid.uuid4(),
            client_id=c_uuid,
            title=clean_title,
            doc_type=item.get("doc_type", doc_type),
            format=file_format,
            topic=final_topic,
            subtopic=item.get("subtopic", ""),
            difficulty=item.get("difficulty", "MEDIUM"),
            domain=final_domain,
            tags=tags,
            raw_content=clean_scenario,
            structured_data=clean_item,
            created_at=now,
        )

        if db is not None:
            db.add(doc)

        saved_records.append({
            "id": str(doc.id),
            "title": doc.title,
            "doc_type": item.get("doc_type", doc_type),
            "category": item.get("category", ""),
            "retrieval_summary": item.get("retrieval_summary", ""),
            "topic": doc.topic,
            "subtopic": doc.subtopic,
            "difficulty": doc.difficulty,
            "domain": doc.domain,
            "scenario": clean_scenario,
            "algorithmic_pattern": item.get("algorithmic_pattern", ""),
            "tags": doc.tags,
            "format": doc.format,
            "structured_data": clean_item,
        })

    if db is not None:
        await db.commit()

    return saved_records


async def load_seed_datasets(
    db: Optional[AsyncSession] = None,
    client_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load bundled seed reference files from data/seed_references/.
    - If db is provided: ingest/persist seed records into ReferenceDocument and commit.
    - If db is None: returns the parsed in-memory list of seed items directly.
    """
    c_uuid = client_id or "00000000-0000-0000-0000-000000000001"
    all_records: List[Dict[str, Any]] = []

    if not SEED_DIR.exists():
        return all_records

    seed_files = list(SEED_DIR.rglob("*.*"))

    for fpath in seed_files:
        if fpath.suffix.lower() not in (".json", ".csv", ".md", ".txt", ".pdf", ".docx"):
            continue

        filename = fpath.name
        content_bytes = fpath.read_bytes()
        try:
            detected_doc_type = "DOMAIN_SCENARIO"
            if fpath.suffix.lower() in (".json", ".jsonl"):
                try:
                    raw_json = content_bytes.decode("utf-8", errors="replace")
                    parsed = json.loads(raw_json)
                    if isinstance(parsed, list) and parsed:
                        detected_doc_type = parsed[0].get("doc_type", "DOMAIN_SCENARIO")
                    elif isinstance(parsed, dict):
                        detected_doc_type = parsed.get("doc_type", "DOMAIN_SCENARIO")
                except Exception:
                    pass

            records = await ingest_file_content(
                db=db,
                client_id=str(c_uuid),
                filename=filename,
                content_bytes=content_bytes,
                doc_type=detected_doc_type,
            )
            all_records.extend(records)
        except Exception as e:
            print(f"[Dataset Ingestion] Error seeding file {filename}: {e}")

    return all_records
