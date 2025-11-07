# Bill Text & LLM Processing System

## Overview

Purp now includes a comprehensive system for fetching and processing full bill text for LLM analysis. This enables AI-powered bill summaries, impact analysis, stakeholder identification, and plain language explanations.

## Quick Start

### 1. Install Dependencies
```bash
pip install pdfplumber PyPDF2
```

### 2. Add Database Columns
```bash
python migrate_bill_text.py
```

### 3. Fetch Bill Text
```bash
# Fetch first 10 bills
python fetch_bill_text.py --limit 10

# Fetch all bills
python fetch_bill_text.py

# Fetch specific bills
python fetch_bill_text.py HB101 HB102 HB103
```

### 4. Try the Demo
```bash
python demo_llm_processing.py
```

## What's New

### Database Schema
- `bills.full_text` - Complete bill text extracted from PDFs
- `bills.text_pdf_url` - URL to official bill text PDF
- `bills.summary_pdf_url` - URL to bill summary PDF
- `bills.text_fetched_at` - Timestamp of last fetch

### New Services
- `services/bill_text_fetcher.py` - Fetches and extracts text from PDFs
  - `fetch_bill_full_text()` - Get text for a bill
  - `extract_key_sections()` - Parse bill into sections
  - `prepare_for_llm()` - Format for LLM input
  - `clean_bill_text()` - Normalize text

### New Scripts
- `fetch_bill_text.py` - Populate database with bill text
- `demo_llm_processing.py` - Interactive demo of all features
- `migrate_bill_text.py` - Database migration

### Model Enhancements
- `Bill.get_llm_context()` - Get formatted text for LLM
- `Bill.to_dict()` - Now includes `has_full_text`, PDF URLs

## Usage Examples

### Basic Text Retrieval
```python
from models import Bill

bill = Bill.query.filter_by(bill_number='HB101').first()

if bill.full_text:
    print(f"Words: {len(bill.full_text.split())}")
    print(bill.full_text[:500])
```

### LLM Integration
```python
# Get formatted context (with token limit)
llm_context = bill.get_llm_context(max_length=4000)

# Use with OpenAI
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a legislative analyst."},
        {"role": "user", "content": f"Summarize:\n\n{llm_context}"}
    ]
)
```

### Search by Content
```python
# Find bills about education
education_bills = Bill.query.filter(
    Bill.full_text.isnot(None),
    Bill.full_text.ilike('%education%')
).all()
```

### Extract Sections
```python
from services.bill_text_fetcher import extract_key_sections

sections = extract_key_sections(bill.full_text)
print(sections['enacting_clause'])
print(sections['effective_date'])
print(sections['numbered_sections'])
```

## LLM Use Cases

1. **Bill Summarization** - Generate 2-3 sentence summaries
2. **Impact Analysis** - Identify who is affected and how
3. **Stakeholder Identification** - List affected groups
4. **Plain Language Translation** - Explain in simple terms
5. **Comparison** - Compare similar bills
6. **Semantic Search** - Find bills by meaning, not just keywords

## Architecture

```
┌─────────────────────┐
│ Missouri Legislature│
│   house.mo.gov      │
└──────────┬──────────┘
           │ PDF URLs
           ▼
┌─────────────────────┐
│ bill_text_fetcher.py│
│  - fetch_bill_pdfs  │
│  - extract_text     │
│  - clean_text       │
└──────────┬──────────┘
           │ Cleaned text
           ▼
┌─────────────────────┐
│   Database (bills)  │
│  - full_text        │
│  - text_pdf_url     │
│  - summary_pdf_url  │
└──────────┬──────────┘
           │ Bill data
           ▼
┌─────────────────────┐
│  Bill.get_llm_context()│
│  prepare_for_llm()  │
└──────────┬──────────┘
           │ Formatted
           ▼
┌─────────────────────┐
│   LLM (GPT-4,       │
│   Claude, Llama)    │
└──────────┬──────────┘
           │ Analysis
           ▼
┌─────────────────────┐
│  UI / API Response  │
└─────────────────────┘
```

## File Structure

```
purp/
├── models/__init__.py              # Bill model with get_llm_context()
├── services/
│   └── bill_text_fetcher.py       # Text extraction service
├── fetch_bill_text.py              # CLI tool to populate text
├── demo_llm_processing.py          # Interactive demo
├── migrate_bill_text.py            # Database migration
└── docs/
    └── development/
        ├── bill-text-llm.md        # Full documentation
        └── BILL_TEXT_QUICKSTART.md # Quick start guide
```

## Performance

- **Storage**: ~10-15KB per bill (avg 5,000-15,000 words)
- **Fetch Time**: ~2-5 seconds per bill
- **Database Size**: 100 bills ≈ 1-2 MB
- **LLM Context**:
  - GPT-4: ~6,000 chars ≈ 1,500 tokens
  - Claude: Full text (200k token limit)
  - Local models: ~4,000 chars ≈ 1,000 tokens

## Supported LLMs

### Cloud LLMs
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude 3)
- **Google** (Gemini)
- **Cohere**

### Local LLMs (via Ollama)
- **Llama 2/3**
- **Mistral**
- **Phi-2**
- **Code Llama**

## Next Steps

1. **Choose LLM Provider** - Select OpenAI, Anthropic, or local
2. **Create Analysis Routes** - Add `/api/bills/<id>/analyze` endpoint
3. **Build UI** - Display summaries on bill pages
4. **Cache Results** - Store LLM outputs to avoid re-processing
5. **Automate** - Schedule nightly text fetching
6. **Advanced Features**:
   - Semantic search across bills
   - Bill comparison
   - Amendment tracking
   - Voting prediction

## Documentation

- [Quick Start Guide](docs/development/BILL_TEXT_QUICKSTART.md)
- [Full LLM Guide](docs/development/bill-text-llm.md)
- [Service Documentation](services/bill_text_fetcher.py)

## Examples in Action

```bash
# See it in action
python demo_llm_processing.py

# The demo shows:
# 1. Basic retrieval - Get bill text from database
# 2. LLM formatting - Format text for AI processing
# 3. Section extraction - Parse structured sections
# 4. Prompt generation - Create analysis prompts
# 5. Batch processing - Handle multiple bills
# 6. Content search - Find bills by keywords
```

## Troubleshooting

**No text extracted?**
- Some PDFs may be scanned images (need OCR)
- Check PDF URL is valid
- Ensure pdfplumber is installed

**Import errors?**
```bash
pip install pdfplumber PyPDF2
```

**Database errors?**
```bash
python migrate_bill_text.py
```

## Success! ✓

You now have a complete system for:
- ✅ Fetching full bill text from Missouri Legislature
- ✅ Storing text in database
- ✅ Extracting structured sections
- ✅ Formatting for LLM processing
- ✅ Searching bill content
- ✅ Batch processing

Ready to build AI-powered legislative analysis!
