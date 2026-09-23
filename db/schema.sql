-- ─────────────────────────────────────────────────────────────────────────────
-- Multi-Agent Assessment System — PostgreSQL Schema
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ── CLIENTS ──────────────────────────────────────────────────────────────────
CREATE TABLE clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    api_key_hash    TEXT NOT NULL UNIQUE,
    config          JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE client_preferences (
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    language            TEXT NOT NULL,
    html_template_id    UUID,
    code_template_id    UUID,
    difficulty_bias     FLOAT NOT NULL DEFAULT 0.0
                            CHECK (difficulty_bias BETWEEN -1.0 AND 1.0),
    question_style      TEXT NOT NULL DEFAULT 'standard',
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (client_id, language)
);

-- ── QUESTIONS ─────────────────────────────────────────────────────────────────
CREATE TYPE question_status AS ENUM (
    'PROCESSING',
    'AWAITING_REVIEW',
    'APPROVED',
    'REJECTED',
    'NEEDS_HUMAN_REVIEW'
);

CREATE TABLE questions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id),
    version     INT NOT NULL DEFAULT 1,
    status      question_status NOT NULL DEFAULT 'PROCESSING',
    state       JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX questions_client_status_idx ON questions(client_id, status);
CREATE INDEX questions_created_at_idx ON questions(created_at DESC);

CREATE TABLE question_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    version         INT NOT NULL,
    triggered_by    TEXT,           -- 'client_feedback' | 'quality_fail' | 'initial'
    re_entry_agent  TEXT,           -- 'agent_a' | 'agent_c' | 'agent_d'
    state_snapshot  JSONB NOT NULL,
    state_diff      JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (question_id, version)
);

-- ── REFERENCE QUESTIONS ───────────────────────────────────────────────────────
CREATE TABLE reference_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES clients(id),    -- NULL = global
    topic           TEXT NOT NULL,
    subtopic        TEXT,
    difficulty      TEXT NOT NULL CHECK (difficulty IN ('EASY','MEDIUM','HARD','EXPERT')),
    language        TEXT NOT NULL,
    title           TEXT NOT NULL,
    text            TEXT NOT NULL,
    embedding       VECTOR(1536) NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'APPROVED',
    quality_score   FLOAT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ref_q_embedding_idx
    ON reference_questions
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX ref_q_filter_idx
    ON reference_questions(topic, language, difficulty);

-- ── TOPIC KNOWLEDGE GRAPH ─────────────────────────────────────────────────────
CREATE TABLE topics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL UNIQUE,
    parent_id           UUID REFERENCES topics(id),
    prerequisites       JSONB NOT NULL DEFAULT '[]',
    learning_objectives JSONB NOT NULL DEFAULT '[]',
    embedding           VECTOR(1536),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── TEMPLATES ─────────────────────────────────────────────────────────────────
CREATE TABLE html_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    question_type   TEXT NOT NULL,
    template        TEXT NOT NULL,
    version         INT NOT NULL DEFAULT 1,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE code_templates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    language    TEXT NOT NULL,
    template    TEXT NOT NULL,
    version     INT NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (client_id, language)
);

-- ── TEST CASES ────────────────────────────────────────────────────────────────
CREATE TABLE test_cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    type            TEXT NOT NULL CHECK (type IN ('VISIBLE','HIDDEN')),
    input           TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    description     TEXT,
    covers_edge     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX test_cases_question_idx ON test_cases(question_id);

-- ── FEEDBACK ──────────────────────────────────────────────────────────────────
CREATE TABLE feedback (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         UUID NOT NULL REFERENCES questions(id),
    client_id           UUID NOT NULL REFERENCES clients(id),
    raw_text            TEXT NOT NULL,
    feedback_type       TEXT CHECK (feedback_type IN
                            ('DIFFICULTY','CLARITY','TECHNICAL','FORMAT','SCOPE')),
    severity            TEXT CHECK (severity IN ('LOW','MEDIUM','HIGH')),
    affected_components JSONB NOT NULL DEFAULT '[]',
    re_entry_agent      TEXT,        -- 'agent_a' | 'agent_c' | 'agent_d'
    resolved            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── OBSERVABILITY ─────────────────────────────────────────────────────────────
CREATE TABLE agent_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      UUID NOT NULL,
    question_id     UUID REFERENCES questions(id),
    agent_name      TEXT NOT NULL,      -- 'agent_a', 'agent_c.question_gen', etc.
    model           TEXT NOT NULL,
    prompt_hash     TEXT,
    input_tokens    INT,
    output_tokens   INT,
    cost_usd        FLOAT,
    latency_ms      INT,
    status          TEXT NOT NULL
                        CHECK (status IN ('SUCCESS','FAILED','RETRIED','ESCALATED')),
    retry_count     INT NOT NULL DEFAULT 0,
    internal_step   BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE for Agent C sub-steps
    error_detail    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX agent_runs_question_idx ON agent_runs(question_id);
CREATE INDEX agent_runs_name_idx ON agent_runs(agent_name);

-- ── ROW-LEVEL SECURITY ────────────────────────────────────────────────────────
ALTER TABLE reference_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback             ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_cases          ENABLE ROW LEVEL SECURITY;
ALTER TABLE html_templates      ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_templates      ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_preferences  ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_reference_questions ON reference_questions
    USING (client_id IS NULL OR
           client_id = current_setting('app.current_client_id', TRUE)::UUID);

CREATE POLICY rls_questions ON questions
    USING (client_id = current_setting('app.current_client_id', TRUE)::UUID);

CREATE POLICY rls_feedback ON feedback
    USING (client_id = current_setting('app.current_client_id', TRUE)::UUID);

CREATE POLICY rls_test_cases ON test_cases
    USING (question_id IN (
        SELECT id FROM questions
        WHERE client_id = current_setting('app.current_client_id', TRUE)::UUID
    ));

CREATE POLICY rls_html_templates ON html_templates
    USING (client_id = current_setting('app.current_client_id', TRUE)::UUID);

CREATE POLICY rls_code_templates ON code_templates
    USING (client_id = current_setting('app.current_client_id', TRUE)::UUID);

CREATE POLICY rls_client_preferences ON client_preferences
    USING (client_id = current_setting('app.current_client_id', TRUE)::UUID);

-- ── SEED DATA (for development) ───────────────────────────────────────────────
INSERT INTO clients (id, name, api_key_hash, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Dev Client',
    '$2b$12$placeholder.hash.for.dev.only',
    TRUE
); 