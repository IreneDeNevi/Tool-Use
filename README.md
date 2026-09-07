# Tool-Use Research Pipeline

An open-source research pipeline that turns a natural-language question into a structured Markdown report. The project combines specialized agents, asynchronous web search and crawling, retrieval-augmented generation (RAG), and persistent vector memory.

The pipeline is designed as a practical example of how an LLM can use external tools instead of generating an answer from its context window alone.

## What It Does

Given a research question, the application:

1. Creates a research plan with the `ResearchPlannerAgent`.
2. Sends the plan's search terms to a SearXNG instance.
3. Crawls result pages concurrently with `aiohttp` and extracts readable text with `trafilatura`.
4. Checks `robots.txt` before crawling and skips disallowed pages.
5. Stores plans and extracted pages in ChromaDB using sentence-transformer embeddings.
6. Retrieves relevant passages and asks the `SummaryReportAgent` to produce a Markdown report.

The default LLM integration uses the Hugging Face Inference API. Despite the historical `LocalLLM` class name, inference is remote unless the implementation is replaced with a local model backend.

## Architecture

```text
User question
      |
      v
ResearchPlannerAgent --+--> ChromaDB (research plan)
      |
      v
WebSearchAgent --> SearXNG --> async crawler --> ChromaDB (web pages)
      |
      v
SummaryReportAgent <-- semantic retrieval <-- ChromaDB
      |
      v
summary_report.md
```

The main extension points are:

- `agents/research_planner.py`: converts a question into a JSON research plan.
- `agents/web_search_agent.py`: orchestrates search, crawling, and indexing.
- `agents/summary_agent.py`: builds RAG context and generates the report.
- `tools/web_search.py`: SearXNG client with bounded concurrency and retries.
- `tools/crawel.py`: asynchronous crawler and text extraction.
- `tools/memory.py`: local or HTTP ChromaDB adapter.
- `models/llm.py`: Hugging Face Inference API adapter.

## Requirements

- Python 3.10+ (Python 3.11 is recommended)
- `uv` for dependency management
- Docker and Docker Compose for SearXNG
- A read-only Hugging Face token
- Network access to Hugging Face, SearXNG, and the pages being crawled

The first run also downloads the embedding model configured by `CHROMA_EMBEDDING_MODEL`.
The repository is configured to install the CPU-only PyTorch build. CUDA and an NVIDIA GPU are not required because the LLM is accessed through the Hugging Face Inference API.

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/IreneDeNevi/Tool-Use.git
cd Tool-Use
```

Create an environment and install the locked CPU-only dependencies:

```bash
uv venv --python 3.11
source .venv/bin/activate       # Windows: .venv\Scripts\activate
uv sync
```

The PyTorch source is pinned in `pyproject.toml` to the official CPU wheel index, so `uv sync` does not install NVIDIA CUDA packages.

Create a local environment file from the template:

```bash
cp .env.example .env
```

Set `HUGGINGFACE_HUB_TOKEN` in `.env` to a read-only token. Review `LLM_MODEL_NAME` if a different instruct model is required. Do not commit `.env` or any token.

## Start the Services

Start SearXNG:

```bash
docker compose up -d searxng
docker compose ps
```

SearXNG is available at <http://localhost:8080>. Verify its JSON endpoint before running the pipeline:

```bash
curl "http://localhost:8080/search?q=python&format=json"
```

ChromaDB does not need to be started for the default configuration: the application uses a persistent local client in `./memory_store`. To use the containerized ChromaDB service instead, set these values in `.env`:

```env
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_SSL=false
```

Then start it with `docker compose up -d chromadb`. The application still uses `CHROMA_PERSIST_PATH` when running in local mode.

## Run the Application

Interactive mode:

```bash
uv run python main.py
```

Enter a research question when prompted. The generated report is written to `summary_report.md`.

The package also exposes the `run` entry point:

```bash
uv run run
```

## Test the Full Pipeline

`test_pipeline.py` is an end-to-end smoke test rather than a unit-test suite. It runs three predefined research questions and writes `summary_report_test1.md`, `summary_report_test2.md`, and `summary_report_test3.md`.

Run it after configuring the Hugging Face token and SearXNG:

```bash
uv run python test_pipeline.py
```

The smoke test validates that:

- the planner returns a plan;
- SearXNG returns searchable results;
- pages can be crawled and extracted;
- documents are persisted in ChromaDB;
- the report agent produces non-empty Markdown;
- report files are created on disk.

Before a full network test, run the inexpensive local checks:

```bash
python -m compileall -q agents models tools main.py test_pipeline.py
docker compose config --quiet
```

These checks validate Python syntax and Compose configuration but do not replace the end-to-end smoke test.

## Configuration

Important environment variables are defined in `.env.example`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `SEARXNG_BASE_URL` | SearXNG endpoint | `http://localhost:8080` |
| `SEARXNG_SECRET` | Optional SearXNG request header | empty |
| `SEARXNG_LANGUAGE` | Search language | unset |
| `SEARXNG_ENGINES` | Comma-separated engine list | SearXNG defaults |
| `HUGGINGFACE_HUB_TOKEN` | Authentication for inference | required |
| `LLM_MODEL_NAME` | Hugging Face instruct model | `mistralai/Mistral-7B-Instruct-v0.3` |
| `CHROMA_HOST` | Remote ChromaDB host; empty means local | empty |
| `CHROMA_PORT` | Remote ChromaDB port | `8000` |
| `CHROMA_PERSIST_PATH` | Local ChromaDB directory | `./memory_store` |
| `CHROMA_COLLECTION` | ChromaDB collection name | `research-cache` |
| `CHROMA_EMBEDDING_MODEL` | Sentence-transformer model | `sentence-transformers/all-MiniLM-L6-v2` |

To clear local vector memory and start fresh:

```bash
rm -rf memory_store
```

## Project Structure

```text
.
├── agents/                 # Planner, search, summary, and base agent classes
├── models/                 # LLM integration
├── tools/                  # Search, crawler, and vector-memory adapters
├── searxng/                # SearXNG configuration and runtime data
├── docker-compose.yml      # SearXNG and optional ChromaDB services
├── main.py                 # Interactive application entry point
├── test_pipeline.py        # End-to-end smoke test
└── pyproject.toml          # Dependencies and tool configuration
```

## Design Decisions and Trade-offs

- **Agents have focused responsibilities.** Planning, retrieval, and summarization can be changed independently.
- **Async I/O is used where it matters.** Search requests and page downloads are bounded by semaphores, avoiding an unbounded request burst.
- **ChromaDB provides durable semantic memory.** The pipeline can reuse indexed content between runs instead of keeping all context in one prompt.
- **SearXNG avoids coupling the application to a single search provider.** Search engines can be selected through configuration.
- **The current LLM client is synchronous.** `LocalLLM.achat` is intended as an asynchronous compatibility layer, but the main planner and summarizer still call synchronous inference. A production version could use an async provider or move blocking inference to a worker.

## Responsible Crawling

Only crawl sources whose terms permit it. The crawler checks `robots.txt` by default, identifies itself with a user agent, uses request timeouts, and limits concurrency. This is a technical safeguard, not a substitute for reviewing the terms of each website.

## Troubleshooting

### `HUGGINGFACE_HUB_TOKEN is not set`

Create `.env`, add a read-only Hugging Face token, and make sure the application is started from the repository root.

### No search results are returned

Check that SearXNG is running and that `SEARXNG_BASE_URL` points to the correct endpoint. Inspect logs with:

```bash
docker compose logs -f searxng
```

### Hugging Face SSL or proxy errors

Corporate TLS interception can block Hugging Face requests. Use a trusted CA configuration provided by your organization or run the project in GitHub Codespaces. Do not disable certificate verification globally.

### The first run is slow

The embedding model and other ML dependencies may be downloaded and initialized on the first run. Subsequent runs reuse the local cache.

## Technical Interview Talking Points

This project demonstrates:

- decomposition of an LLM workflow into explicit agent responsibilities;
- tool calling through a search API and a crawler;
- asynchronous I/O with bounded concurrency;
- RAG backed by persistent vector storage;
- configuration through environment variables;
- service orchestration with Docker Compose;
- defensive parsing when an LLM returns imperfect JSON;
- responsible crawling with `robots.txt`, timeouts, and request limits.

Useful improvement directions include adding unit tests with mocked SearXNG and LLM clients, structured observability, source-level citations in the report, retry policies for inference, and an asynchronous LLM implementation.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
