# Research Agents (Open-Source)

Pipeline **open‑source** per ricerche web con **agenti**, **memoria a lungo termine** (ChromaDB) e **concorrenza** via `asyncio`.

## Caratteristiche
- **LLM locale** (HuggingFace Transformers) – facilmente sostituibile (Mistral, Llama, Phi‑3, ecc.)
- **ResearchPlannerAgent** → crea piano di ricerca
- **WebSearchAgent (async)** → ricerche in parallelo con Brave API + **crawl4ai** per l'estrazione dei contenuti
- **SummaryReportAgent** → genera un **report Markdown** con RAG dalla memoria
- **Memoria a lungo termine** con **ChromaDB** (persistenza su disco)
- Architettura **modulare** per sostituire modelli e tool

>  **Nota legale**: prima di effettuare crawling di un sito, verifica sempre Termini d'Uso e `robots.txt` del dominio. Il crawler qui può rispettare automaticamente `robots.txt`.

---

## Requisiti
- Python **3.10+** (consigliato 3.11)
- [uv](https://github.com/astral-sh/uv) (gestore dipendenze veloce)
- Chiave API **Brave Search** (`BRAVE_API_KEY`) – registrati su Brave per ottenerla
- (Opzionale) GPU NVIDIA con driver + CUDA per performance dei modelli

### Dipendenze principali
- `transformers`, `accelerate`, `torch`
- `sentence-transformers`, `chromadb`
- `aiohttp`, `tenacity`, `python-dotenv`
- `crawl4ai`

---

##  Setup rapido

1. **Clona** il repository e posizionati nella cartella del progetto.

2. **Crea l'ambiente** e installa le dipendenze con **uv**:
   ```bash
   uv venv -p 3.11
   source .venv/bin/activate  # su Windows: .venv\\Scripts\\activate
   uv sync  # genera anche uv.lock se assente
   ```

   > **Torch**: su alcune piattaforme potresti voler installare una build specifica (CPU/GPU). Vedi istruzioni ufficiali PyTorch e scegli l'indice corretto. Esempio CPU-only:
   > ```bash
   > pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
   > ```

3. **Configura l'ambiente**
   - Crea un file `.env` nella root del progetto con:
     ```env
     BRAVE_API_KEY=la_tua_chiave_brave
     ```

4. **Struttura del progetto** (sintesi)
   ```text
   project/
   ├── agents/
   │   ├── base_agent.py
   │   ├── research_planner.py
   │   ├── web_search_agent.py
   │   └── summary_agent.py
   ├── tools/
   │   ├── memory.py
   │   ├── web_search.py
   │   └── crawler.py
   ├── models/
   │   └── llm.py
   ├── main.py
   ├── pyproject.toml
   └── README.md
   ```

---

## ▶️ Esecuzione

Esegui l'applicazione:
```bash
uv run python main.py
```

Flusso:
1. Inserisci la **richiesta di ricerca**.
2. Il **ResearchPlannerAgent** genera un **piano** e lo salva in **ChromaDB**.
3. Il **WebSearchAgent** esegue ricerche e **crawl** in parallelo (`asyncio`) e salva estratti in memoria.
4. Il **SummaryReportAgent** costruisce un **report Markdown** con contenuti rilevanti dalla memoria (RAG) e lo salva in `summary_report.md`.

---

## 🧠 Memoria a lungo termine (ChromaDB)
- Persistenza in `./memory_store`.
- Salviamo piani di ricerca, pagine web estratte e report.
- Recupero semantico via `SentenceTransformer` (all‑MiniLM‑L6‑v2).

Per pulire la memoria:
```bash
rm -rf memory_store/
```

---

##  Cambiare modello LLM
Modifica `models/llm.py` e sostituisci `model_name` con un altro **instruct model** (es. `meta-llama/Meta-Llama-3-8B-Instruct`, `microsoft/Phi-3-mini-4k-instruct`). Verifica i requisiti hardware del modello scelto.

---

## Test rapidi
- Aumenta la concorrenza del crawler o della ricerca modificando `concurrency` in `tools/web_search.py` e `tools/crawler.py`.
- Imposta `respect_robots=True/False` nel crawler (consigliato `True` in produzione).

---

##  Note su uv.lock
Questo progetto usa **uv**. Il file **`uv.lock`** è specifico della risoluzione delle dipendenze nel tuo ambiente. Per generarlo/aggiornarlo in modo affidabile:
```bash
uv lock  # oppure semplicemente `uv sync`
```
> Non includiamo qui un `uv.lock` pre‑generato per evitare discrepanze tra piattaforme (Linux/Mac/Windows) e varianti di Torch.

---

##  Troubleshooting
- **Torch non si installa**: usa l'indice ufficiale PyTorch per la tua piattaforma (CPU/GPU) e ripeti `uv sync`.
- **BRAVE_API_KEY mancante**: assicurati di avere la chiave nell'ambiente o in `.env`.
- **Crawl lento**: riduci `urls` o aumenta `concurrency` con moderazione; attenzione ai limiti del sito target.

---

##  Licenza
MIT
