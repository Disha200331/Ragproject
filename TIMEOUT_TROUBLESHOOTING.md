# RAG Pipeline - Timeout Troubleshooting Guide

## ❌ Problem: httpx.ReadTimeout Error

```
httpx.ReadTimeout: Failed to read response...
```

This error means **Ollama is taking too long to respond** when generating knowledge graph entities.

---

## 🔍 Root Causes

### 1. **Gemma3:1b is Slow on CPU**
   - gemma3:1b is a 1B parameter model
   - On CPU (no GPU), it can take 2-5 minutes per chunk
   - Default timeout was 10 minutes (600 seconds)
   - With 50 chunks, this can exceed the timeout

### 2. **CPU is Overloaded**
   - Other programs running
   - System low on RAM
   - Background processes using CPU

### 3. **Large PDF Processing**
   - Each chunk contains lots of text
   - Model struggles to extract relationships
   - Request times out before completing

---

## ✅ Solutions (Try in Order)

### Solution 1: Use FAST MODE (Recommended for CPU)
```bash
python rag_pipeline_fast.py
```

**What it does:**
- Uses tinyllama:latest (10x faster!)
- Processes only 20 chunks instead of 50
- Extracts only 1 relationship per chunk
- Smaller chunk size (256 tokens)
- Shorter timeout (5 minutes for fast failure)

**Expected time:** 2-10 minutes

---

### Solution 2: Reduce PAGE_LIMIT in .env
```ini
PAGE_LIMIT=10
```

Edit `.env` and change:
- `PAGE_LIMIT=50` → `PAGE_LIMIT=10` (test with fewer chunks first)

**How it helps:**
- Fewer chunks = less processing time
- Timeout is per chunk, not total
- Can test with 10 chunks = ~20-50 minutes total

```bash
python rag_pipeline.py
```

---

### Solution 3: Increase Timeout

Edit `rag_pipeline.py` line ~70:

```python
# BEFORE:
request_timeout=600.0  # 10 minutes

# AFTER:
request_timeout=3600.0  # 60 minutes
```

**Note:** Already fixed to 1800 (30 minutes) in latest version

---

### Solution 4: Reduce Relationships Per Chunk

Edit `rag_pipeline.py` line ~215:

```python
# BEFORE:
max_paths_per_chunk=3

# AFTER:
max_paths_per_chunk=1  # Minimum = faster
```

**Effect:**
- 1 relationship per chunk = fastest
- 2-3 relationships = balanced
- 5+ relationships = slowest

---

### Solution 5: Install GPU (Ultimate Fix)

If you have an NVIDIA GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Gemma3:1b will use GPU (50-100x faster!)
python rag_pipeline.py
```

---

## 📋 Quick Comparison

| Approach | Time | Accuracy | Effort |
|----------|------|----------|--------|
| Fast Mode | 2-10 min | Medium | ⭐ Easy |
| PAGE_LIMIT=10 | 20-50 min | High | ⭐ Easy |
| Reduce paths=1 | 30-60 min | Medium | ⭐ Easy |
| Increase timeout | 1-2 hours | High | ⭐ Easy |
| GPU + Full | 5-10 min | High | ⭐⭐⭐ Hard |

---

## 🚀 Recommended Quick Start

### For Immediate Results (2-10 minutes):
```bash
python rag_pipeline_fast.py
```

### For Better Accuracy (30-60 minutes):
```bash
# Edit .env:
PAGE_LIMIT=20

# Then run:
python rag_pipeline.py
```

### For Production (1-2 hours on CPU, 5-10 min with GPU):
```bash
# Edit .env:
PAGE_LIMIT=0

# Then run:
python rag_pipeline.py
```

---

## 🔧 Advanced Tuning

### For Very Slow Systems:

1. **Edit .env:**
```ini
PAGE_LIMIT=5
```

2. **Edit rag_pipeline.py (line ~215):**
```python
kg_extractor = SimpleLLMPathExtractor(
    llm=llm,
    max_paths_per_chunk=1,  # Minimum
    num_workers=1,
)
```

3. **Run:**
```bash
python rag_pipeline.py
```

---

### For Balanced Approach:

1. **Edit .env:**
```ini
PAGE_LIMIT=25
MAX_PATHS_PER_CHUNK=2
```

2. **Run:**
```bash
python rag_pipeline.py
```

---

## 📊 Performance Expectations

### CPU Baseline (Windows, i7, no GPU):
- **tinyllama:** 1-2 minutes per 5 chunks
- **gemma3:1b:** 5-10 minutes per 5 chunks

### With GPU (NVIDIA):
- **tinyllama:** 10-30 seconds per 5 chunks
- **gemma3:1b:** 1-2 minutes per 5 chunks

### With High-End GPU (RTX 4090):
- **tinyllama:** 2-5 seconds per 5 chunks
- **gemma3:1b:** 10-30 seconds per 5 chunks

---

## ✅ Verify Setup After Fix

```bash
# Quick test to ensure everything works
python quick_test.py

# Verify Ollama is responsive
curl http://localhost:11434/api/tags

# Check Neo4j connection
python verify_setup.py
```

---

## 📝 What Changed

### Fixed in `rag_pipeline.py`:
- ✅ Timeout increased: 600s → 1800s (30 minutes)
- ✅ Added retry logic (auto-retry on timeout)
- ✅ Better timeout error handling
- ✅ Detailed troubleshooting messages

### New Files:
- ✅ `rag_pipeline_fast.py` - Fast alternative pipeline
- ✅ Updated `.env` - Better configuration
- ✅ This troubleshooting guide

---

## 🆘 Still Timing Out?

If you're still getting timeouts:

1. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   Should show: `{"models":[{"name":"gemma3:1b"}]}`

2. **Check system resources:**
   - Open Task Manager
   - CPU usage should be ~90-100%
   - RAM usage should increase (normal)
   - Free disk space > 2GB

3. **Reduce to minimum:**
   ```ini
   # .env
   PAGE_LIMIT=5
   ```

4. **Use fast mode:**
   ```bash
   python rag_pipeline_fast.py
   ```

5. **Check Ollama logs:**
   - Ollama window should show generation progress
   - If stuck: restart Ollama
   ```bash
   ollama serve
   ```

---

## 💡 Pro Tips

1. **Don't close Ollama window** - It needs to stay running
2. **Close other apps** - Free up CPU for Ollama
3. **Don't interrupt script** - Let it run, even if slow
4. **Monitor progress** - Watch Ollama window for model thinking
5. **Start small** - Test with PAGE_LIMIT=5 first

---

**Need help?** Try: `python quick_test.py` to verify everything works!
