"""
Question Schema Registry & Machine-Verifiable Validation Models.
Enforces the 3-dimensional classification matrix and category-specific contracts.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Type
from pydantic import BaseModel, Field, field_validator, ValidationError


class Subject(str, Enum):
    DSA = "DSA"
    GENERAL_PROGRAMMING = "GENERAL_PROGRAMMING"
    SQL = "SQL"
    ORACLE = "ORACLE"
    DATA_SCIENCE = "DATA_SCIENCE"
    AI_ML = "AI_ML"


class QuestionFormat(str, Enum):
    GENERAL_CODING = "GENERAL_CODING"
    DATABASE_QUERY = "DATABASE_QUERY"
    DATASET_CODING = "DATASET_CODING"
    OBJECTIVE_MCQ = "OBJECTIVE_MCQ"


class EvaluationMode(str, Enum):
    STDIN_STDOUT = "STDIN_STDOUT"
    RESULT_SET_MATCH = "RESULT_SET_MATCH"
    PYTHON_RUNNER = "PYTHON_RUNNER"
    ANSWER_KEY = "ANSWER_KEY"


class OperationalMode(str, Enum):
    SOURCE_PRESERVATION = "SOURCE_PRESERVATION"
    QUESTION_GENERATION = "QUESTION_GENERATION"


# ─────────────────────────────────────────────────────────────────────────────
# Category Schema Definitions
# ─────────────────────────────────────────────────────────────────────────────

class GeneralCodingSchema(BaseModel):
    title: str = Field(..., min_length=3)
    category: str = Field(default="DSA")
    doc_type: str = Field(default="AUTHORING_SPEC")
    format_schema: str = Field(default=QuestionFormat.GENERAL_CODING.value)
    evaluation_mode: str = Field(default=EvaluationMode.STDIN_STDOUT.value)
    scenario: str = Field(..., min_length=15)
    action_prompt: str = Field(default="")
    function_name: str = Field(default="solution")
    function_description: str = Field(default="")
    input_format: str = Field(default="")
    sample_input_annotated: str = Field(default="")
    constraints: List[str] = Field(..., min_length=1)
    output_format: str = Field(default="")
    sample_output: str = Field(default="")
    explanation: str = Field(default="")
    html_template: str = Field(default="")
    starter_code_snippets: Dict[str, str] = Field(default_factory=dict)
    solution_code: Dict[str, str] = Field(default_factory=dict)
    test_cases: List[dict] = Field(..., min_length=1)

    @field_validator("constraints")
    @classmethod
    def validate_constraints_mandatory(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("COD_CONSTRAINTS_REQUIRED: Constraints section is mandatory for coding questions.")
        for item in v:
            if not str(item).strip():
                raise ValueError("COD_CONSTRAINTS_EMPTY: Empty constraint string encountered.")
        return v

    @field_validator("test_cases")
    @classmethod
    def validate_test_cases(cls, v: List[dict]) -> List[dict]:
        if not v or len(v) == 0:
            raise ValueError("COD_TEST_CASES_REQUIRED: At least one test case must be defined.")
        has_visible = any(
            t.get("type") in ("VISIBLE", "SAMPLE") or t.get("is_sample")
            for t in v
        )
        if not has_visible:
            raise ValueError("COD_VISIBLE_TEST_REQUIRED: At least 1 visible/sample test case is required.")
        return v


class SQLQuestionSchema(BaseModel):
    title: str = Field(..., min_length=3)
    category: str = Field(default="SQL")
    doc_type: str = Field(default="AUTHORING_SPEC")
    format_schema: str = Field(default=QuestionFormat.DATABASE_QUERY.value)
    evaluation_mode: str = Field(default=EvaluationMode.RESULT_SET_MATCH.value)
    scenario: str = Field(..., min_length=15)
    schema_definition: str = Field(..., min_length=10)
    sample_data: str = Field(..., min_length=10)
    query_instructions: str = Field(default="")
    expected_output_columns: List[str] = Field(default_factory=list)
    sample_output_table: str = Field(default="")
    explanation: str = Field(default="")
    starter_code_snippets: Dict[str, str] = Field(default_factory=dict)
    solution_code: Dict[str, str] = Field(..., min_length=1)
    test_cases: List[dict] = Field(default_factory=list)

    @field_validator("solution_code")
    @classmethod
    def validate_sql_solution_readonly(cls, v: Dict[str, str]) -> Dict[str, str]:
        sql = (v.get("sql") or v.get("oracle") or "").strip().upper()
        if not sql:
            raise ValueError("SQL_SOLUTION_REQUIRED: Working SQL solution query is required.")
        forbidden_keywords = ["DROP ", "DELETE ", "UPDATE ", "ALTER ", "TRUNCATE ", "INSERT "]
        for kw in forbidden_keywords:
            if kw in sql:
                raise ValueError(f"SQL_MUTATING_STATEMENT: SQL assessment queries cannot contain '{kw}'. Must be SELECT or CTE.")
        if not sql.startswith("SELECT") and not sql.startswith("WITH"):
            raise ValueError("SQL_MUST_BE_SELECT: Solution query must begin with SELECT or WITH.")
        return v


class DataScienceSchema(BaseModel):
    title: str = Field(..., min_length=3)
    category: str = Field(default="DATA_SCIENCE")
    doc_type: str = Field(default="AUTHORING_SPEC")
    format_schema: str = Field(default=QuestionFormat.DATASET_CODING.value)
    evaluation_mode: str = Field(default=EvaluationMode.PYTHON_RUNNER.value)
    scenario: str = Field(..., min_length=15)
    dataset_description: str = Field(..., min_length=10)
    function_name: str = Field(default="process_data")
    function_description: str = Field(default="")
    input_format: str = Field(default="")
    sample_input: str = Field(default="")
    output_format: str = Field(default="")
    sample_output: str = Field(default="")
    tolerance: float = Field(default=1e-4)
    explanation: str = Field(default="")
    starter_code_snippets: Dict[str, str] = Field(default_factory=dict)
    solution_code: Dict[str, str] = Field(..., min_length=1)
    test_cases: List[dict] = Field(default_factory=list)


class AIObjectiveSchema(BaseModel):
    title: str = Field(..., min_length=3)
    category: str = Field(default="AI_ML")
    doc_type: str = Field(default="AUTHORING_SPEC")
    format_schema: str = Field(default=QuestionFormat.OBJECTIVE_MCQ.value)
    evaluation_mode: str = Field(default=EvaluationMode.ANSWER_KEY.value)
    scenario: str = Field(..., min_length=15)
    question_prompt: str = Field(..., min_length=5)
    options: List[str] = Field(..., min_length=2)
    correct_answer: str = Field(..., min_length=1)
    explanation: str = Field(default="")
    taxonomy_tag: str = Field(default="AI_CONCEPTS")


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher & Validator Function
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
    "DSA": GeneralCodingSchema,
    "GENERAL_PROGRAMMING": GeneralCodingSchema,
    "CORE_ALGORITHMS": GeneralCodingSchema,
    "SQL": SQLQuestionSchema,
    "ORACLE": SQLQuestionSchema,
    "DATA_SCIENCE": DataScienceSchema,
    "AI_ML": AIObjectiveSchema,
}


def get_schema_for_category(category: str) -> Type[BaseModel]:
    """Returns the registered Pydantic validation schema for a given category."""
    cat_upper = (category or "DSA").strip().upper()
    return CATEGORY_SCHEMA_MAP.get(cat_upper, GeneralCodingSchema)


def validate_question_data(category: str, data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[BaseModel]]:
    """
    Validates question content against its category contract.
    Returns: (is_valid: bool, error_messages: List[str], parsed_model: Optional[BaseModel])
    """
    schema_cls = get_schema_for_category(category)
    try:
        instance = schema_cls(**data)
        return True, [], instance
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Validation error")
            errors.append(f"[{loc}] {msg}")
        return False, errors, None
