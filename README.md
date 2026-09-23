# Multi-Agent Assessment Generation System

Consolidated 7-agent workflow for generating personalized coding assessment questions.

## Quick Start

```bash
# 1. Install dependencies
pip install uv && uv sync

# 2. Copy and fill env vars
cp .env.example .env

# 3. Start infrastructure
docker compose up postgres redis -d

# 4. Run API (dev mode)
make api

# 5. Run worker (separate terminal)
make worker