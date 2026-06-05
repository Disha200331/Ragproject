# RAG Pipeline - Startup Guide

## Prerequisites

The RAG pipeline requires three services running:

1. **Neo4j** - Graph database (✅ Already running on your system)
2. **Ollama** - LLM server (❌ NOT RUNNING - Fix required)
3. **Python Environment** - Virtual environment (✅ Ready)

---

## Step 1: Start Ollama

### If Ollama is NOT installed:
1. Download from: https://ollama.ai
2. Install and launch the application
3. Continue to Step 2

### If Ollama IS installed:
Open a **new PowerShell terminal** and run:
```powershell
ollama serve
```

This will start the Ollama server on `http://localhost:11434`

---

## Step 2: Download Gemma2 Model (One-time setup)

Open a **second PowerShell terminal** and run:
```powershell
ollama pull gemma2
```

This downloads the Gemma2 model (may take 5-10 minutes depending on internet speed)

---

## Step 3: Verify Services

In your project directory, run the diagnostic:
```powershell
python diagnose.py
```

Expected output:
```
✅ Data directory exists
✅ Neo4j credentials configured
✅ Successfully connected to Neo4j
✅ Ollama is running
✅ Embedding model loaded successfully
```

---

## Step 4: Run the RAG Pipeline

Once all services are running:
```powershell
python rag_pipeline.py
```

The script will:
1. Initialize the Gemma2 LLM
2. Load the BGE embedding model (1-2 minutes first time)
3. Load documents from `data/` folder
4. Build a knowledge graph in Neo4j
5. Answer sample questions

---

## Troubleshooting

### Error: "Ollama is not running"
- Ensure `ollama serve` is running in a separate terminal
- Check firewall settings (allow port 11434)

### Error: "Failed to connect to Neo4j"
- Start Neo4j using: `neo4j-community-2026.05.0\bin\neo4j.bat`
- Verify credentials in `.env` file

### Error: "No documents loaded"
- Add PDF files to the `data/` folder
- Currently has: `annual report pdf.pdf`

### Script taking too long?
- BGE embeddings load slowly on first run (CPU/GPU dependent)
- Ollama model inference is slow on CPU (consider GPU for faster processing)

---

## Performance Notes

- **First run**: Expect 5-15 minutes (model downloads + processing)
- **Subsequent runs**: 1-3 minutes (cached models)
- **Optimal setup**: GPU support (CUDA/Metal) significantly speeds up inference

To enable GPU support in Ollama, visit: https://ollama.ai/docs
