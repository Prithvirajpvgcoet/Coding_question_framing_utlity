export type QuestionStatus =
  | "PROCESSING"
  | "AWAITING_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "NEEDS_HUMAN_REVIEW"
  | "QA_FAILED"
  | "CANCELLED"
  | "UPLOAD_QUEUED"
  | "UPLOADED";

export interface TestCase {
  id?: string;
  type: "VISIBLE" | "HIDDEN";
  input_args: string | Record<string, any>;
  expected_output: string | Record<string, any>;
  points?: number;
  explanation?: string;
}

export interface TestExecutionResult {
  test_index: number;
  passed: boolean;
  actual_output?: string;
  expected_output?: string;
  error?: string;
  execution_time_ms?: number;
}

export interface QuestionRequirements {
  topic: string;
  subtopic?: string;
  difficulty: "EASY" | "MEDIUM" | "HARD" | "EXPERT" | string;
  question_type: "ALGORITHMIC" | "DEBUG" | "FILL_IN_BLANK" | "SQL" | string;
  target_language: string;
  max_solve_time_minutes?: number;
  custom_constraints?: string[];
  raw_request?: string;
}

export interface QuestionMetadata {
  title: string;
  topics?: string[];
  purpose?: string;
  tags?: string[];
  author?: string;
}

export interface QuestionHTML {
  formatted_question: string;
  instructions?: string;
  examples_html?: string;
}

export interface QuestionCode {
  language: string;
  solution: string;
  stub?: string;
  hints?: string[];
}

export interface QualityAssessment {
  pass: boolean;
  avg_score: number;
  scores: {
    clarity?: number;
    edge_cases?: number;
    efficiency?: number;
    formatting?: number;
    relevance?: number;
    [key: string]: number | undefined;
  };
  failure_reasons?: string[];
  scorer_feedback?: string;
}

export interface FinalQA {
  approved: boolean;
  aggregate_score?: number;
  deterministic_checks: {
    html_valid?: boolean;
    sandbox_passed?: boolean;
    required_fields?: boolean;
    no_duplicates?: boolean;
    [key: string]: boolean | undefined;
  };
}

export interface QuestionState {
  request_id: string;
  question_id: string;
  client_id: string;
  version: number;
  status: QuestionStatus;
  current_agent: string;
  retry_counts?: Record<string, number>;
  internal_retry_count?: number;
  revision_count?: number;
  requirements: QuestionRequirements;
  question?: QuestionMetadata;
  html?: QuestionHTML;
  code?: QuestionCode;
  test_cases?: TestCase[];
  execution?: {
    passed: boolean;
    unverified?: boolean;
    results?: TestExecutionResult[];
    error?: string;
  };
  quality?: QualityAssessment;
  final_qa?: FinalQA;
  agent_run_ids?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface QuestionSummary {
  question_id: string;
  status: QuestionStatus;
  version: number;
  topic: string;
  difficulty: string;
  language: string;
  created_at: string | null;
}

export interface AgentRunStep {
  id: string;
  agent_name: string;
  model: string;
  internal_step: boolean;
  status: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
  error_detail?: string;
  created_at: string | null;
}

export interface RunDetails {
  run_id: string;
  question_id: string;
  status: QuestionStatus;
  state: QuestionState | null;
  version: number;
  steps: AgentRunStep[];
  created_at: string | null;
  updated_at: string | null;
}

export interface DashboardStats {
  generated: number;
  qa_passed: number;
  awaiting_review: number;
  approved: number;
  needs_review: number;
  processing: number;
  upload_queued: number;
  uploaded: number;
  breakdown: Record<string, number>;
}

export interface QuestionBankItem {
  id: string;
  name: string;
  description?: string;
  imocha_bank_id?: string;
  question_count: number;
  created_at: string | null;
}

export interface SSEProgressEvent {
  type: "progress" | "agent_complete" | "error" | "done";
  current_agent: string;
  message: string;
  state?: Partial<QuestionState>;
}

export interface ReferenceDocumentItem {
  id: string;
  title: string;
  doc_type: string;
  format: string;
  topic: string;
  subtopic: string;
  difficulty: string;
  domain: string;
  tags: string[];
  raw_content?: string;
  structured_data?: any;
  created_at?: string;
}
