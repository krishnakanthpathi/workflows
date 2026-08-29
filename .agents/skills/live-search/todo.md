# Live Search & Research Toolkit: TODO & Roadmap

This document outlines the known issues, target query categories, and an incremental, feature-by-feature execution roadmap for transforming `live-search` into a robust, multi-engine research toolkit.

---

## 1. Identified Issues & Limitations

| # | Issue | Description | Impact |
| :--- | :--- | :--- | :--- |
| **1** | **Single Point of Failure** | Relies entirely on a single upstream endpoint (`html.duckduckgo.com`). No fallback mechanism if rate-limited, CAPTCHA-blocked, or if HTML markup changes. | High fragility; queries fail completely when blocked. |
| **2** | **Shallow Information Depth** | Returns only 1–2 sentence snippets (~150 chars). Cannot read full article text, section headers, tables, or extract structured research data. | Insufficient for deep research, paper reviews, or complex inquiries. |
| **3** | **No Domain-Specific Research Engines** | Lacks dedicated academic paper discovery (ArXiv, OpenAlex, Europe PMC), encyclopedia lookups (Wikipedia), or developer discussion search (HackerNews). | General web search misses academic papers, citation counts, and tech discussions. |
| **4** | **No Multi-Engine Aggregator & Concurrency** | Unable to query multiple sources in parallel, blend search results, deduplicate links, or rank relevance. | Limited coverage and higher risk of missing key sources. |
| **5** | **No Benchmarking & Evaluation Suite** | Lacks automated metrics to measure latency (P50/P90), success rates, content depth, and error recovery across query types. | No quantitative way to verify reliability, speed, and accuracy improvements. |

---

## 2. Research & Search Query Categories

The enhanced search toolkit and benchmark suite will support and evaluate four distinct research categories:

### A. General Knowledge
- **Focus**: Broad factual queries, overviews, everyday information, definitions.
- **Example Queries**:
  - `history of the printing press impact on literacy`
  - `difference between nuclear fusion and fission`
  - `renewable energy adoption rates global 2025`
- **Target Source**: General Web (DDG HTML / DDG Lite) + Wikipedia.

### B. Academic & Scientific Research
- **Focus**: Peer-reviewed papers, scientific breakthroughs, preprints, citation counts, author lists, and open-access PDFs.
- **Example Queries**:
  - `transformer self-attention mechanism multi-head latent attention`
  - `CRISPR prime editing advances in genetic therapies`
  - `mixture of experts load balancing without auxiliary loss`
- **Target Source**: OpenAlex, Europe PMC, arXiv API (extracts titles, authors, publication years, abstracts, DOIs, PDFs).

### C. Technical, Libraries & Programming
- **Focus**: Developer documentation, API signatures, package changelogs, architecture deep-dives, GitHub repositories, developer troubleshooting.
- **Example Queries**:
  - `python 3.14 free-threaded build GIL removal status`
  - `sqlite WAL mode concurrent read write performance`
  - `uv package manager workspace dependency resolution`
- **Target Source**: Developer docs, HackerNews Algolia, GitHub search, tech engineering blogs.

### D. Live & Recent Facts
- **Focus**: Real-time information, release versions, breaking news, schedules, contact numbers, status updates.
- **Example Queries**:
  - `gas booking in india number for hp in ap`
  - `latest stable release of PyTorch and CUDA support matrix`
  - `DeepSeek V3 benchmark results and release date`
- **Target Source**: Fast live web search with fresh indexing.

---

## 3. Incremental Feature-by-Feature Roadmap

### 🏁 Step 1: Benchmark Suite & Baseline Measurements
- [ ] Create `scripts/benchmark_search.py` to test latency (ms), reliability (%), result depth, and error handling.
- [ ] Benchmark existing baseline (`scripts/live_search.py`) across all 4 categories.
- [ ] Benchmark standalone alternative zero-token endpoints (DDG Lite, Wikipedia API, OpenAlex, Europe PMC, HackerNews).
- [ ] Produce initial comparison metrics table.

---

### 🌐 Step 2: Resilient General Web Engine & Fallback Mechanism
- [x] Enhance general web search to support automatic fallback (DDG HTML -> DDG Lite).
- [x] Add robust regex and HTML unescaping for edge cases (encoded characters, special entities).
- [x] Add Wikipedia overview card and summary integration.
- [x] Add timeout safeguards and zero-token standard library architecture.

---

### 🎓 Step 3: Academic & Scientific Paper Search Mode (`-a` / `--academic`)
- [ ] Integrate zero-API-key academic engines: **OpenAlex API** + **Europe PMC API** + **arXiv API**.
- [ ] Extract structured research metadata:
  - Paper title
  - Author list
  - Year & Journal / Conference
  - Full Abstract
  - Citation count & DOI
  - Direct Open-Access PDF / Landing Page link
- [ ] Add `--academic` (or `-a`) CLI flag and JSON format support.

---

### 📖 Step 4: Encyclopedic & Fact Verification Engine (`-w` / `--wiki`)
- [ ] Integrate Wikipedia OpenSearch & Summary extraction API.
- [ ] Extract clean article definitions, section summaries, and disambiguated topics.
- [ ] Add `--wiki` (or `-w`) CLI flag.

---

### 💻 Step 5: Technical & Developer Discussion Search (`-t` / `--tech`)
- [ ] Integrate Hacker News Algolia Search API for technical discussions, post-mortems, and engineering blog posts.
- [ ] Extract post titles, discussion points, URLs, point scores, and comments count.
- [ ] Add `--tech` (or `-t`) CLI flag.

---

### 📄 Step 6: Deep Page Reader & Markdown Content Extractor (`--read` / `--deep`)
- [x] Build a zero-dependency HTML-to-clean-Markdown extractor (`HTMLToMarkdownParser`).
- [x] Clean boilerplate (navbars, scripts, stylesheets, sidebars, cookie banners, footers).
- [x] Extract structured headings, paragraphs, bullet points, and code snippets.
- [x] Support `--read <url>` to fetch full readable content for any link.
- [x] Support `--deep <N>` to automatically search and deep-read top N results in a single command for comprehensive research.
- [x] Support `--json`, `--sources-only`, `--max-chars`, and `--full` options.

---

### 🔀 Step 7: Multi-Engine Aggregator & Blended Ranking (`-m` / `--multi`)
- [ ] Implement parallel asynchronous fetching across multiple engines using `concurrent.futures`.
- [ ] Deduplicate overlapping URLs and blend results with relevance scoring.
- [ ] Add `--multi` (or `-m`) CLI flag.

---

### 📚 Step 8: Documentation, Readme & Guide Updates
- [ ] Create a comprehensive [README.md](file:///Users/krishnakanth/Projects/workflow/.agents/skills/live-search/README.md) for the live-search skill.
- [ ] Update [SKILL.md](file:///Users/krishnakanth/Projects/workflow/.agents/skills/live-search/SKILL.md) with all new flags, research modes, and subagent schemas.
- [ ] Update [references/search-guide.md](file:///Users/krishnakanth/Projects/workflow/.agents/skills/live-search/references/search-guide.md) with research query best practices and benchmark results.
