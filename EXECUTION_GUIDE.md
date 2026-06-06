# RAG Pipeline - Execution Guide

## 📋 Summary of Changes Made

### 1. **Improved Error Handling**
   - Better error messages with specific instructions
   - Windows event loop policy for async compatibility
   - Connection validation before proceeding

### 2. **Better Output & Logging**
   - ✓/✗ indicators for success/failure
   - Execution time tracking
   - Summary of processed items
   - Progress indicators throughout

### 3. **Configuration from .env**
   - All settings now configurable via .env
   - PAGE_LIMIT configurable (set to 0 for all pages)
   - Temperature, context window, model names configurable

### 4. **Enhanced File Handling**
   - Supports both .pdf and .txt files
   - Shows file sizes in MB
   - Better path handling for Windows

### 5. **New Helper Scripts**
   - `verify_setup.py` - Check all dependencies
   - `quick_test.py` - Test connections without full pipeline

---

## 🚀 Quick Start (3 Steps)

### Step 1: Verify Setup
```bash
python verify_setup.py
```
This checks:
- ✓ Python version
- ✓ All required packages
- ✓ PDF files in data/
- ✓ .env configuration
- ✓ Ollama & Neo4j services (optional)

### Step 2: Start Services
Open **TWO** terminals:

**Terminal 1 - Start Ollama:**
```bash
ollama serve
```
Wait for it to start (shows port 11434)

**Terminal 2 - Start Neo4j:**
```bash
restart_neo4j.bat
```
Wait for it to complete

### Step 3: Run Pipeline
```bash
python rag_pipeline.py
```

---

## 📊 Expected Output

When successful, you'll see:

```
======================================================================
  RAG PIPELINE - KNOWLEDGE GRAPH BUILDER
  Running at: 2026-06-06 10:30:45
======================================================================

[1/6] Importing LlamaIndex modules...
[2/6] Initializing Models...
   ✓ Ollama is running with 1 model(s)
      - gemma3:1b
   ✓ Ollama LLM (gemma3:1b) initialized
   ✓ BGE embeddings loaded
   ✓ Models initialized successfully

[3/6] Loading Documents...
   ✓ Loaded 145 document chunks

[4/6] Connecting to Neo4j...
   ✓ Neo4j graph store initialized

[5/6] Building Knowledge Graph...
   Processing 50 chunks with gemma3:1b...
   Creating PropertyGraphIndex...
   ✓ Knowledge Graph built successfully!
   ✓ Time taken: 8m 23s
   ✓ Committed to Neo4j

[6/6] Creating Query Engine...
   ✓ Query engine created successfully

======================================================================
  TEST QUERIES - Knowledge Graph RAG Pipeline
======================================================================

  Q: What was Axis Bank's consolidated RoA and Net NPA for fiscal 2025?
  A: [Answer from knowledge graph...]

  Q: Who is the Managing Director & CEO of Axis Bank?
  A: [Answer from knowledge graph...]

======================================================================
  ✓ PIPELINE COMPLETED SUCCESSFULLY!
======================================================================

  📊 Summary:
     - Processed 50 document chunks
     - Built knowledge graph in Neo4j
     - Executed 2 test queries
     - All queries completed successfully

  🔗 Next Steps:
     - Neo4j Browser: http://localhost:7474
     - Username: neo4j
     - Verify: python check_knowledge_graph.py
     - Run more queries: python query_chatbot.py
```

---

## 🔧 Configuration (.env)

Edit `.env` to customize:

```ini
# Neo4j Configuration
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=Disha@2003
NEO4J_URL=bolt://localhost:7687

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b

# LLM Settings
LLM_TEMPERATURE=0.1          # Lower = more deterministic
LLM_CONTEXT_WINDOW=4096      # Token context

# Document Processing
PAGE_LIMIT=50                # 0 = process all pages

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_MAX_LENGTH=512
```

---

## 🐛 Troubleshooting

### Issue: "Ollama is not running"
```
Solution: Start Ollama in another terminal
$ ollama serve
```

### Issue: "Neo4j connection failed"
```
Solution: Start Neo4j
$ restart_neo4j.bat
```

### Issue: "No PDF files found in data/"
```
Solution: Add PDF files to data/ directory
- Place your PDFs in: data/
- Supported formats: .pdf, .txt
```

### Issue: "gemma3:1b not found"
```
Solution: Pull the model
$ ollama pull gemma3:1b
```

### Issue: "Import error: ModuleNotFoundError"
```
Solution: Install dependencies
$ pip install -r requirements.txt
```

### Issue: "Import error: nest_asyncio"
```
Solution: Optional but helpful for compatibility
$ pip install nest_asyncio
```

---

## 📈 Performance Notes

- **First run**: 1-2 minutes (downloads BGE embeddings ~500MB)
- **Processing PDFs**: 5-30 minutes depending on:
  - PDF size
  - Number of pages
  - CPU speed
  - PAGE_LIMIT setting

- **Tips for faster execution**:
  - Lower PAGE_LIMIT (default: 50)
  - Close other applications
  - Use GPU if available (configure torch)
  - Reduce max_paths_per_chunk in code

---

## 📚 Files Included

| File | Purpose |
|------|---------|
| `rag_pipeline.py` | Main pipeline (IMPROVED) |
| `verify_setup.py` | Check dependencies (NEW) |
| `quick_test.py` | Test connections (NEW) |
| `.env` | Configuration file |
| `requirements.txt` | Python dependencies |
| `restart_neo4j.bat` | Start Neo4j |
| `data/` | Place PDF files here |

---

## ✅ Next Steps After Success

1. **View Knowledge Graph**:
   - Open: http://localhost:7474
   - Login: neo4j / Disha@2003
   - Explore nodes and relationships

2. **Run Custom Queries**:
   ```bash
   python check_knowledge_graph.py
   ```

3. **Test More Queries**:
   Edit the test queries in `rag_pipeline.py`:
   ```python
   ask_chatbot("Your custom question here?")
   ```

4. **Run Full Pipeline** (all pages):
   - Edit `.env`: `PAGE_LIMIT=0`
   - Run: `python rag_pipeline.py`
   - Run overnight (5-30 min processing time)

---

## 📝 Notes

- All changes are documented in code with `[OK]`, `✓`, `✗` markers
- Async compatibility improved for Windows
- Better error messages for debugging
- Configurable parameters via .env
- Support for both PDF and text files
- Progress tracking with time estimates

---

**Ready to run?** Execute: `python rag_pipeline.py`
