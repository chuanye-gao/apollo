# Apollo

[English](README.md) | [中文](README.zh-CN.md)

Apollo is a Chinese Tool Router reproduction project for a 150-tool environment. It implements an engineering-focused two-stage routing pipeline: embedding-based Top-K tool recall first, followed by LLM arbitration and argument extraction only within the recalled candidates.

The project focuses on reproducibility, evaluation, and deployment readiness. It does not execute real tools.

## Highlights

- 150 tools managed by a unified YAML schema.
- 850 Chinese natural-language evaluation samples.
- Two-stage routing: semantic recall plus LLM arbitration.
- Local offline demo mode with hash embeddings and a deterministic dry-run arbiter.
- Evaluation metrics for Top-1 Accuracy, Top-K Recall, Slot Precision / Recall / F1, None Accuracy, and per-category accuracy.
- Baseline comparison for keyword matching, embedding-only routing, full-prompt arbitration, and Apollo two-stage routing.
- CLI, FastAPI REST API, Docker demo, and embedding cache support.

## Architecture

```text
User query
  -> BGE / hash embedding recall
  -> Top-K candidate tools
  -> LLM / dry-run arbitration within candidates
  -> Structured JSON route result
```

Output format:

```json
{
  "is_instruction": true,
  "tool_code": "message.send",
  "intent": "发送消息",
  "arguments": {
    "recipient": "张三",
    "content": "我晚点到"
  },
  "missing_required_arguments": [],
  "confidence": 0.99,
  "reason": "dry-run 本地仲裁"
}
```

## Repository Layout

```text
apollo/
  cache.py          # embedding cache read/write
  cli.py            # command-line interface
  config.py         # YAML tool schema loader
  embedding.py      # BGE and hash embedding models
  evaluate.py       # evaluation and baseline comparison
  llm.py            # OpenAI-compatible client and dry-run arbiter
  prompt.py         # arbitration prompt builder
  retrieval.py      # Top-K tool retriever
  router.py         # end-to-end router
  server.py         # FastAPI REST API
configs/
  tools.yaml        # 150 tool definitions
data/
  generated_queries.jsonl
scripts/
  generate_assets.py
tests/
  test_router.py
```

## Quick Start

Install the project:

```bash
python -m pip install -e .
```

Run the offline smoke test. This mode does not need a BGE model download or an API key:

```bash
python -m apollo.cli route --embedding hash --llm dry-run "请帮我发送消息，收件人：张三，内容：我晚点到"
```

Example output:

```json
{
  "is_instruction": true,
  "tool_code": "message.send",
  "intent": "发送消息",
  "arguments": {
    "recipient": "张三",
    "content": "我晚点到"
  },
  "missing_required_arguments": [],
  "confidence": 0.99,
  "reason": "dry-run 本地仲裁"
}
```

Show retrieved candidates:

```bash
python -m apollo.cli route --embedding hash --llm dry-run --show-candidates "请帮我查询天气，地点：上海，日期：明天"
```

## Production Mode

Production mode uses BGE embeddings and an OpenAI-compatible Chat Completions API.

```bash
set APOLLO_LLM_API_KEY=your_api_key
set APOLLO_LLM_MODEL=your_model
set APOLLO_LLM_BASE_URL=https://api.openai.com/v1

router route "请帮我创建日程，标题：周会安排，日期：明天，时间：明天下午三点"
```

Precompute tool embeddings to reduce startup cost:

```bash
router precompute
```

The cache is stored at `data/tool_embeddings.json` and is automatically invalidated when `configs/tools.yaml` changes.

## Tool Schema

Tool definitions are stored in `configs/tools.yaml`. Each tool contains:

- `code`
- `name`
- `category`
- `description`
- `aliases`
- `examples`
- `arguments`

The current schema contains 150 tools across system tools, office tools, communication tools, life services, multimedia, smart home, developer tools, knowledge tools, and the `none` fallback.

The `none` tool represents non-instruction inputs such as chat, factual questions, explanations, and thanks.

## Evaluation Dataset

The evaluation set is stored in `data/generated_queries.jsonl`.

Current scale:

- 850 total samples
- 149 executable tools covered
- 105 `none` samples
- At least 5 samples per executable tool

Sample types include standard complete instructions, colloquial instructions, ambiguous but routable expressions, missing-argument expressions, and non-instruction distractors.

Regenerate the tool schema and dataset:

```bash
python scripts/generate_assets.py
```

## Evaluation

Run the offline evaluation:

```bash
python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl
```

The evaluator reports Top-1 Accuracy, Top-K Recall for K = 3 / 5 / 8 / 10, Slot Precision / Recall / F1, None Accuracy, per-category accuracy, baseline comparison, and estimated prompt tokens / cost for the full-prompt baseline.

## Current Offline Results

The following results were produced with `hash` embedding and `dry-run` arbitration on the generated 850-sample dataset:

```text
Dataset size:       850
Tool count:         150
None samples:       105

Top-1 Accuracy:     99.65%
Top-3 Recall:       100.00%
Top-5 Recall:       100.00%
Top-8 Recall:       100.00%
Top-10 Recall:      100.00%

Slot Precision:     100.00%
Slot Recall:        100.00%
Slot F1:            100.00%

None Accuracy:      97.14%
```

Per-category accuracy:

```text
System tools:       100.00%
Office tools:       100.00%
Communication:      100.00%
Life services:      100.00%
Multimedia:         100.00%
Smart home:         100.00%
Developer tools:    100.00%
Knowledge tools:    100.00%
None fallback:       97.14%
```

Baseline comparison:

```text
Keyword baseline
  Top-1 Accuracy:   99.18%
  None Accuracy:    93.33%
  Slot F1:          100.00%

Embedding only
  Top-1 Accuracy:   87.65%
  None Accuracy:     0.00%
  Slot F1:            0.00%

LLM full prompt
  Top-1 Accuracy:   99.65%
  None Accuracy:    97.14%
  Slot F1:          100.00%
  Estimated prompt tokens: 14801
  Estimated cost:   $1.887 / 850 samples

Apollo two-stage
  Top-1 Accuracy:   99.65%
  None Accuracy:    97.14%
  Slot F1:          100.00%
```

These offline numbers are intended as a deterministic engineering smoke test and baseline. Real BGE plus real LLM performance should be measured with the same command by switching to `--embedding bge --llm openai`.

## REST API

Install server dependencies:

```bash
python -m pip install -e ".[serve]"
```

Start the demo API:

```bash
set APOLLO_EMBEDDING=hash
set APOLLO_LLM_MODE=dry-run
uvicorn apollo.server:app --reload
```

Endpoints:

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/route` | Route a query and return structured JSON |

Request example:

```bash
curl -s -X POST http://localhost:8000/route ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"请帮我发送消息，收件人：张三，内容：我晚点到\"}"
```

## Docker Demo

Run the no-key local demo:

```bash
docker-compose --profile demo up --build
```

Run production mode:

```bash
copy .env.example .env
docker-compose --profile prod up --build
```

Demo mode uses hash embeddings and dry-run arbitration. Production mode uses BGE embeddings and an OpenAI-compatible LLM.

## Tests

```bash
python -m pytest tests/ -v
```

Current result:

```text
5 passed
```

## Resume-Friendly Summary

Apollo is a Chinese Tool Router reproduction project at 150-tool scale. It implements a two-stage routing pipeline with embedding-based Top-K recall and LLM arbitration, builds a YAML-managed tool schema and an 850-sample Chinese evaluation set, measures Top-K Recall, Tool Accuracy, Slot F1, and None Accuracy, and compares keyword, embedding-only, full-prompt, and two-stage baselines. The project includes CLI, FastAPI, Docker demo, embedding cache, and deterministic dry-run smoke testing for a complete reproducible engineering loop.
