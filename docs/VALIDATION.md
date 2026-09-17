# Validation and Testing Strategy

This document explains how the project was tested, why the testing is structured this way, and which checks were executed to validate the system’s behavior in production-like conditions.

## 1. Testing philosophy

This project is designed around an evidence-first workflow:

- the model must not answer from memory alone,
- a query must trigger live search,
- retrieved sources must be indexed,
- the final summary must be grounded in retrieved material,
- the system must fail safely when evidence is missing instead of producing a black-box answer.

This is a critical design choice for a portfolio-grade AI system because it makes the project auditable, explainable, and resilient to silent hallucination.

---

## 2. Testing objectives

The validation strategy covers four objectives:

1. Functional correctness of the core modules
2. Regression protection against black-box behavior
3. Validity of the live search layer with a real SearXNG backend
4. End-to-end validation of the research pipeline

---

## 3. Test structure

The project follows a layered validation model.

### Level 1 — unit-level validation
This checks isolated functions and contracts:

- plan schema validity
- settings loading
- model factory creation
- search result schema
- domain filter logic
- quality heuristic behavior
- planner normalization logic
- result ranking logic
- HTML export output

These tests are implemented in tests/test_refactor.py.

### Level 2 — regression validation
This guards against failures that are easy to miss in AI systems:

- query phrases like “What is Python...” being treated as valid search terms,
- no-source summaries being scored as strong,
- time-range filtering causing empty search results even when the plain query would work,
- silent fallback to unsupported answers.

### Level 3 — backend validation
This validates the live search engine behavior directly:

- SearXNG is checked with real HTTP requests,
- query formulation is tested against the actual backend response,
- temporal filters are inspected to ensure they are not masking valid results.

### Level 4 — end-to-end validation
This validates the full workflow:

- planner generates a research plan,
- search layer retrieves evidence,
- sources are ranked and crawled,
- summary is produced with citations,
- quality score is computed,
- HTML export is generated.

---

## 4. Environment used for validation

The validation was executed in the project virtual environment and against the local SearXNG service.

Required environment:

- Python virtual environment in the project root
- local SearXNG instance running on localhost:8080
- Hugging Face model access configured for the provider layer

The key validation commands were:

```bash
cd /workspaces/Tool-Use
source .venv/bin/activate
python -m pytest -q tests/test_refactor.py
```

and a live pipeline check:

```bash
cd /workspaces/Tool-Use
source .venv/bin/activate
python - <<'PY'
import asyncio
from app.orchestrator import ResearchOrchestrator

async def main():
    q = 'What is Python and why is it used in data engineering?'
    o = ResearchOrchestrator()
    result = await o.run(q)
    print('RESULT_COUNT:', len(result['search_results']))
    print('GROUND_SCORE:', result['quality']['groundedness_score'])
    print('SUMMARY_HEAD:', result['summary'][:600])

asyncio.run(main())
PY
```

---

## 5. What was actually tested

### A. Planner normalization
The planner previously generated phrase-level queries such as:

- “what is python and why is it used in data engineering”

These are poor search terms for SearXNG. The validation confirmed genuine backend behaviour:

- query `python` → returns results
- query `python data engineering` → often empty
- query `What is Python and why is it used in data engineering?` → not suitable as a search term

This led to a specific normalization rule: reduce questions to a short, high-signal keyword while removing stop words and sentence framing.

### B. Time-range fallback
The real backend issue was not the planner alone. SearXNG returned zero results for valid queries when the pipeline asked for `time_range="year"`.

Validation showed:

- `python` without a time filter → valid result
- `python` with `time_range=year` → zero results

This is why the fallback was introduced: when the filtered request is empty, the system retries without the time filter before stopping.

### C. Black-box prevention
The system was explicitly designed to avoid generating summary output when no sources are available.

This is a guardrail and is essential to prevent the project from looking convincing while being unsupported by evidence.

### D. Quality scoring
The quality heuristic checks whether the report includes actual evidence and citations, not just structure.

It rewards:

- explicit source references,
- source-backed citations,
- section structure,
- summary presence,
- match between cited sources and source URLs.

It also correctly returns a zero groundedness score when there are no sources.

### E. Export workflow
The final pipeline also validates that result artifacts can be exported in formats appropriate for portfolio presentation:

- markdown summary,
- ranked search results JSON,
- HTML report,
- PDF export stub (generated as a report artifact in the runtime directory).

---

## 6. Validation evidence

The following results were actually observed during the final verification run.

### Automated test suite
Command executed:

```bash
cd /workspaces/Tool-Use && . .venv/bin/activate && python -m pytest -q tests/test_refactor.py
```

Observed result:

```text
11 passed in 0.99s
```

### Live pipeline validation
Command executed:

```bash
cd /workspaces/Tool-Use && . .venv/bin/activate && python - <<'PY'
import asyncio
from app.orchestrator import ResearchOrchestrator

async def main():
    q = 'What is Python and why is it used in data engineering?'
    o = ResearchOrchestrator()
    result = await o.run(q)
    print('RESULT_COUNT:', len(result['search_results']))
    print('GROUND_SCORE:', result['quality']['groundedness_score'])
    print('SUMMARY_HEAD:', result['summary'][:600])

asyncio.run(main())
PY
```

Observed result:

```text
RESULT_COUNT: 1
GROUND_SCORE: 0.95
```

This validates that the pipeline is not only structurally correct, but also operationally grounded in a real retrieved source.

---

## 7. Why this testing is structured correctly

This project is not validated by “single happy-path output”. It is validated by checking the full chain of reasoning and evidence:

1. the user query is transformed into search terms,
2. those terms are compatible with the search backend,
3. the backend returns live sources,
4. the sources are ranked and retrieved,
5. the summary is grounded in source material,
6. the output is scored and exported,
7. regressions are prevented by unit tests.

This is exactly the kind of testing pattern expected in serious AI systems and portfolio-grade ML engineering projects.

---

## 8. Recommended usage for future validation

For future work, the project should keep this validation rhythm:

- run unit tests after each change,
- validate planner normalization against real search backend behavior,
- check quality score on end-to-end runs,
- confirm that no summary is generated without evidence,
- keep validation output archived in the runs directory.

This ensures that future upgrades remain transparent and do not silently regress into black-box behavior.

---

## 9. Conclusion

The testing strategy is deliberately evidence-first and structurally layered. It proves not only that the code works, but that the system behaves responsibly when evidence is weak or absent.

That combination is one of the strongest qualities a portfolio project can demonstrate.
