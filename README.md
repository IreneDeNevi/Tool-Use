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
- `crawl4ai` – web scraping con Playwright
- `searxng` – metasearch engine (container Docker)

### Strumenti aggiuntivi
- **Docker & Docker Compose** – per eseguire SearXNG container
- **SearXNG** – metasearch engine in esecuzione su `http://localhost:8080`

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

2b. **Configura Crawl4AI** (web scraper con browser):
   ```bash
   uv run crawl4ai-setup
   uv run python -m playwright install chromium
   uv run crawl4ai-doctor  # verifica installazione
   ```

3. **Configura l'ambiente**
   - Crea un file `.env` nella root del progetto con:
     ```env
     BRAVE_API_KEY=la_tua_chiave_brave
     ```

4. **Avvia SearXNG (metasearch engine)**
   ```bash
   docker compose up -d searxng
   # Accedi a http://localhost:8080
   docker compose logs searxng -f  # monitoraggio log
   ```
   > SearXNG è un metasearch engine open-source che aggrega risultati da più motori di ricerca. I volumi sono persistenti in `./searxng/data` e `./searxng/settings.yml`.

5. **Struttura del progetto** (sintesi)
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
   │   └── crawel.py              # web crawler con Crawl4AI
   ├── models/
   │   └── llm.py
   ├── searxng/
   │   ├── settings.yml           # configurazione SearXNG
   │   └── data/                  # cache persistente
   ├── docker-compose.yml         # servizio SearXNG
   ├── main.py
   ├── pyproject.toml
   ├── .env.example              # template variabili ambiente
   └── README.md
   ```

---

##  Esecuzione

### Avvia i servizi
```bash
# 1. Avvia SearXNG (metasearch engine)
docker compose up -d searxng

# 2. Esegui l'applicazione principale
uv run python main.py
```

### Flusso di esecuzione:
1. Inserisci la **richiesta di ricerca**.
2. Il **ResearchPlannerAgent** genera un **piano di ricerca** e lo salva in **ChromaDB**.
3. Il **WebSearchAgent** esegue ricerche tramite **Brave Search API** o **SearXNG**.
4. Il **crawler** (Crawl4AI) estrae il contenuto dalle pagine web in parallelo (`asyncio`).
5. I contenuti estratti vengono salvati in memoria persistente con embeddings semantici.
6. Il **SummaryReportAgent** costruisce un **report Markdown** con RAG dalla memoria e lo salva in `summary_report.md`.

### Arresto dei servizi
```bash
docker compose down
```

---

##  Memoria a lungo termine (ChromaDB)
- Persistenza in `./memory_store`.
- Salviamo piani di ricerca, pagine web estratte e report.
- Recupero semantico via `SentenceTransformer` (all‑MiniLM‑L6‑v2).

Per pulire la memoria:
```bash
rm -rf memory_store/
```

##  SearXNG (Metasearch Engine)
**SearXNG** è un motore di ricerca privato, decentralizzato e open-source che aggrega risultati da multiple fonti.

- **Configurazione**: [searxng/settings.yml](searxng/settings.yml)
- **Accesso**: `http://localhost:8080`
- **Storage**: Dati persistenti in `./searxng/data`

### Cmdline utili
```bash
# Status del container
docker compose ps

# Log real-time
docker logs -f searxng

# Accedi alla bash del container
docker exec -it searxng bash

# Test della ricerca API
curl "http://localhost:8080/search?q=test&format=json" | jq .
```

##  Web Crawler (Crawl4AI)
**Crawl4AI** fornisce estrazione di contenuti web con:
- Browser headless Chromium via Playwright
- Parsing JavaScript e dynamic content
- Supporto per PDF, MHTML, screenshot export
- Gestione robots.txt

Implementazione in [tools/crawel.py](tools/crawel.py).

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

### Setup Crawl4AI
- **Chromium non installa**: assicurati di avere le librerie di sistema per Chromium: `sudo apt-get install libxcomposite1 libxdamage1 libxfixes3 libxrandr2`
- **"Executable doesn't exist"**: esegui `uv run python -m playwright install chromium` per reinstallare il browser.

### SearXNG Container
- **Errore "Invalid settings.yml"**: Verifica che [searxng/settings.yml](searxng/settings.yml) sia valido. Rigenerato dal container se mancante.
- **Porta 8080 in uso**: Cambia in [docker-compose.yml](docker-compose.yml) da `8080:8080` a `8081:8080`.
- **Container in restart loop**: Controlla log con `docker logs searxng --tail 50`.

### Generale
- **Torch non si installa**: usa l'indice ufficiale PyTorch per la tua piattaforma (CPU/GPU) e ripeti `uv sync`.
- **BRAVE_API_KEY mancante**: assicurati di avere la chiave nell'ambiente o in `.env`.
- **Crawl lento**: riduci `urls` o aumenta `concurrency` con moderazione; attenzione ai limiti del sito target.

---

##  Licenza
MIT

