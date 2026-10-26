import json
import re
from typing import Optional, List, Dict, Any
from agents.base import groq_chat, load_prompt, MODEL_STRONG

SYSTEM = load_prompt("agent_c_question_gen")

def _clean_json(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return cleaned.strip()

def build_platform_markdown(data: dict) -> str:
    title = data.get("title", "Element Removal")
    scenario = data.get("scenario", "")
    action_prompt = data.get("action_prompt", "Find the minimum number of elements removed.")
    function_name = data.get("function_name", "elementRemoval")
    goal = data.get("goal", "minimum number of elements removed")
    input_format = data.get("input_format", "The first line contains an integer N...")
    sample_input = data.get("sample_input_annotated", "5  -- denotes N")
    constraints = data.get("constraints_list", data.get("constraints", ["1 <= N <= 1000"]))
    output_format = data.get("output_format", "The output contains an integer denoting the minimum number of elements removed.")
    sample_output = data.get("sample_output", "1")
    bullets = data.get("explanation_bullets", [])
    bullets_md = "\n".join(f"- {b}" for b in bullets) if bullets else f"- Output = {sample_output}"
    exp_text = data.get("explanation_text", "")

    constraints_md = "\n".join(constraints) if isinstance(constraints, list) else str(constraints)

    md = f"""# {title}

{scenario}

**{action_prompt}**

### Function Description
In the provided code snippet, implement the provided `{function_name}(...)` method to find the {goal}. You can write your code in the space below the phrase **"WRITE YOUR LOGIC HERE"**.

There will be multiple test cases running, so the Input and Output should match exactly as provided.
The base Output variable `result` is set to a default value `-404` which can be modified. Additionally, you can add or remove these output variables.

### Input Format
{input_format}

### Sample Input
```text
{sample_input}
```

### Constraints
{constraints_md}

### Output Format
{output_format}

### Sample Output
```text
{sample_output}
```

### Explanation
Given:
{bullets_md}

{exp_text}

Hence, the output is **{sample_output}**.
"""
    return md

def build_platform_html(data: dict) -> str:
    title = data.get("title", "Element Removal")
    scenario = data.get("scenario", "")
    action_prompt = data.get("action_prompt", "Find the minimum number of elements removed.")
    function_name = data.get("function_name", "elementRemoval")
    goal = data.get("goal", "minimum number of elements removed")
    input_format = data.get("input_format", "The first line contains an integer N...")
    sample_input = data.get("sample_input_annotated", "5  -- denotes N")
    constraints = data.get("constraints_list", data.get("constraints", ["1 <= N <= 1000"]))
    output_format = data.get("output_format", "The output contains an integer denoting the minimum number of elements removed.")
    sample_output = data.get("sample_output", "1")
    # Bullets formatting guard
    bullets = data.get("explanation_bullets", [])
    if isinstance(bullets, str):
        # If model returned a string with HTML or newlines instead of a list
        cleaned_bullets = [re.sub(r"^[-*•\s<>/a-z0-9]+", "", b).strip() for b in bullets.splitlines() if b.strip()]
        bullets = [b for b in cleaned_bullets if len(b) > 1]
    elif isinstance(bullets, list):
        cleaned_bullets = []
        for b in bullets:
            b_str = str(b).strip()
            # If item is broken down into single characters or html tags, skip
            if len(b_str) <= 1 or b_str in ("<ul>", "</ul>", "<li>", "</li>"):
                continue
            cleaned_bullets.append(b_str)
        bullets = cleaned_bullets

    bullets_html = "".join(f"<li>{b}</li>\n" for b in bullets) if bullets else f"<li>Result = {sample_output}</li>"
    bullets_md = "\n".join(f"- {b}" for b in bullets) if bullets else f"- Result = {sample_output}"
    exp_text = data.get("explanation_text", "")
    if isinstance(exp_text, list):
        exp_text = " ".join(str(x) for x in exp_text)
    exp_text_html = exp_text.replace("\n", "<br />\n")

    # Constraints cleaning guard
    if isinstance(constraints, list):
        constraints_list_clean = [re.sub(r"^[-*•\s<>/a-z0-9]+", "", str(c)).strip() for c in constraints]
        constraints_list_clean = [c for c in constraints_list_clean if len(c) > 1 and c not in ("<ul>", "</ul>", "<li>", "</li>")]
        constraints_html = "<br />\n".join(constraints_list_clean) if constraints_list_clean else "1 <= N <= 1000"
        constraints_md = "\n".join(constraints_list_clean) if constraints_list_clean else "1 <= N <= 1000"
    else:
        constraints_str = str(constraints).replace("<ul>", "").replace("</ul>", "").replace("<li>", "").replace("</li>", "\n")
        constraints_html = constraints_str.replace("\n", "<br />\n")
        constraints_md = constraints_str

    # Format sample input lines with non-breaking spaces before '-- denotes'
    sample_lines = []
    for line in sample_input.splitlines():
        if "-- denotes" in line:
            parts = line.split("-- denotes")
            left = parts[0].strip()
            right = parts[1].strip()
            sample_lines.append(f"{left}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<em>-- denotes <strong>{right}</strong></em>")
        else:
            sample_lines.append(line)
    annotated_sample_box = "<br />\n".join(sample_lines)

    html = f"""<em><strong>{title}</strong></em><br />
<br />
{scenario}<br />
<br />
<em><strong>{action_prompt}</strong></em><br />
<br />
<!--[if--><strong><u>Function Description</u></strong><br />
In the provided code snippet, implement the provided <strong><code>{function_name}(...)</code></strong>method to find {goal}.&nbsp;You can write your code in the space below the phrase <code><strong>&ldquo;</strong><strong>WRITE YOUR LOGIC HERE</strong><strong>&rdquo;</strong></code>.<br />
<br />
There will be multiple test cases running, so the Input and Output should match exactly as provided.<br />
The base Output variable <code><strong>result</strong></code> is set to a default value <code><strong>-404</strong></code> which can be modified. Additionally, you can add or remove these output variables.<br />
<br />
<strong><u>Input Format</u></strong><br />
{input_format}<br />
<!--[if--><br />
<strong><u>Sample Input</u></strong><br />
<div style="background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;">{annotated_sample_box}</div>
<br />
<strong><u>Constraints</u></strong><br />
{constraints_html}<br />
<br />
<strong><u>Output Format</u></strong><br />
{output_format}<br />
<br />
<strong><u>Sample Output</u></strong><br />
<div style="background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;">{sample_output}</div>
&nbsp;<br />
<strong><u>Explanation</u></strong><br />
Given<br />
<ul>
{bullets_html}
</ul>
{exp_text}<br />
<br />
Hence, the output is <em><strong>{sample_output}</strong></em>.<!--!--><!--[endif]--><!--[if--><!--[endif]--><!--!--><!--[if-->"""
    return html

async def generate(blueprint: dict, references: Optional[List[Dict[str, Any]]] = None) -> dict:
    prompt_payload = {
        "blueprint": blueprint,
    }
    if references:
        # Stage 1: Extract AUTHORING_SPEC (always first item from Agent B's 3-stage retrieval)
        authoring_spec = None
        domain_refs = []
        for ref in references:
            if ref.get("doc_type") == "AUTHORING_SPEC":
                authoring_spec = ref
            else:
                domain_refs.append(ref)

        if authoring_spec:
            # Pass the formatting rules so LLM knows the platform standard
            prompt_payload["authoring_spec"] = {
                "standard_format_rules": authoring_spec.get("standard_format_rules", {}),
                "starter_code_snippets_available": list(authoring_spec.get("starter_code_snippets", {}).keys()),
                "test_cases_count": len(authoring_spec.get("test_cases", [])),
                "example_scenario": authoring_spec.get("scenario", ""),
            }
            # Store for later use in HTML/code building
            prompt_payload["_authoring_spec_full"] = authoring_spec

        prompt_payload["domain_references"] = [
            {"title": r.get("title"), "domain": r.get("domain"), "scenario": r.get("scenario")}
            for r in domain_refs[:3]
        ]

    user_prompt = f"""Generate the complete official assessment question matching the exact platform authoring specification:
{json.dumps(prompt_payload)}

Return a JSON object containing ALL of:
"title", "scenario", "goal", "action_prompt", "function_name", "input_format", "output_format", "constraints_list", "sample_input_annotated", "sample_output", "explanation_bullets", "explanation_text"
"""

    content, usage = await groq_chat(
        model=MODEL_STRONG,
        system=SYSTEM,
        user=user_prompt,
        agent_name="agent_c.question_gen",
        json_mode=True
    )
    
    data = {}
    try:
        data = json.loads(_clean_json(content))
    except Exception:
        pass

    # Merge blueprint fields as fallback
    for k in ("title", "scenario", "goal", "action_prompt", "function_name", "input_format", "output_format", "sample_input_annotated", "sample_output", "explanation_bullets", "explanation_text"):
        if not data.get(k) and blueprint.get(k):
            data[k] = blueprint.get(k)

    if not data.get("constraints_list") and blueprint.get("constraints"):
        data["constraints_list"] = blueprint.get("constraints")

    title = data.get("title") or blueprint.get("title") or "Element Removal"
    function_name = data.get("function_name") or "elementRemoval"

    # Construct the authoritative platform markdown & HTML directly
    platform_md = build_platform_markdown(data)
    platform_html = build_platform_html(data)

    examples = [
        {
            "input": data.get("sample_input_annotated", "5\n2\n1 1 1 2 2"),
            "output": str(data.get("sample_output", "1")),
            "explanation": data.get("explanation_text", "")
        }
    ]

    # Extract code stubs from authoring_spec references if available
    code_stubs = {}
    _spec = prompt_payload.get("_authoring_spec_full", {})
    if _spec:
        raw_stubs = _spec.get("starter_code_snippets", {})
        fn = function_name
        for lang, stub_template in raw_stubs.items():
            if isinstance(stub_template, str):
                code_stubs[lang] = stub_template.replace("{{function_name}}", fn)

    return {
        "title": title,
        "function_name": function_name,
        "description_markdown": platform_md,
        "description_html": platform_html,
        "purpose": data.get("scenario", "") or platform_md[:150],
        "examples": examples,
        "constraints_list": data.get("constraints_list", ["1 <= N <= 1000"]),
        "raw_platform_data": data,
        "code_stubs": code_stubs,
    }
