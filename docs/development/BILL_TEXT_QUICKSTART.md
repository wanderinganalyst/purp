# Bill Text & LLM Quick Start

Get started with bill text fetching and LLM processing in 5 minutes.

## 1. Install Dependencies

```bash
source .venv/bin/activate
pip install pdfplumber PyPDF2
```

## 2. Run Database Migration

```bash
python init_db.py
```

This adds the new columns to store bill text:
- `full_text` - Complete bill text
- `text_pdf_url` - Link to official PDF
- `summary_pdf_url` - Link to summary PDF  
- `text_fetched_at` - Timestamp

## 3. Fetch Bill Text

### Fetch All Bills
```bash
python fetch_bill_text.py
```

### Fetch Specific Bills
```bash
python fetch_bill_text.py HB101 HB102
```

### Fetch First 10 Bills
```bash
python fetch_bill_text.py --limit 10
```

## 4. Run the Demo

```bash
python demo_llm_processing.py
```

This interactive demo shows:
- Basic text retrieval
- LLM-ready formatting
- Section extraction
- Prompt generation
- Batch processing
- Text search

## 5. Use in Code

### Get Bill Text

```python
from models import Bill

bill = Bill.query.filter_by(bill_number='HB101').first()

# Check if text is available
if bill.full_text:
    print(f"Words: {len(bill.full_text.split())}")
    print(bill.full_text[:500])
```

### Format for LLM

```python
# Get formatted context
llm_context = bill.get_llm_context()

# Limit length (for token limits)
llm_context = bill.get_llm_context(max_length=4000)
```

### Extract Sections

```python
from services.bill_text_fetcher import extract_key_sections

sections = extract_key_sections(bill.full_text)
print(sections['enacting_clause'])
print(sections['effective_date'])
```

## 6. Integrate with LLM

### OpenAI Example

```python
import openai

prompt = f"""Summarize this bill in 2-3 sentences:

{bill.get_llm_context(max_length=8000)}

Summary:"""

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a legislative analyst."},
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)
```

### Anthropic Claude Example

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": f"Analyze this bill:\n\n{bill.get_llm_context()}"}
    ]
)

print(message.content[0].text)
```

### Local Model (Ollama)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2
```

```python
import requests

response = requests.post('http://localhost:11434/api/generate',
    json={
        "model": "llama2",
        "prompt": f"Summarize:\n\n{bill.get_llm_context(max_length=4000)}"
    }
)

print(response.json()['response'])
```

## Common Tasks

### Find Bills About a Topic

```python
education_bills = Bill.query.filter(
    Bill.full_text.isnot(None),
    Bill.full_text.ilike('%education%')
).all()

for bill in education_bills:
    print(f"{bill.bill_number}: {bill.title}")
```

### Batch Process Bills

```python
bills = Bill.query.filter(Bill.full_text.isnot(None)).all()

for bill in bills:
    llm_context = bill.get_llm_context(max_length=4000)
    # Send to LLM for analysis
    # Store results
```

### Search by Keywords

```python
keywords = ['tax', 'education', 'healthcare']

for keyword in keywords:
    count = Bill.query.filter(
        Bill.full_text.isnot(None),
        Bill.full_text.ilike(f'%{keyword}%')
    ).count()
    print(f"{keyword}: {count} bills")
```

## Next Steps

1. **Choose an LLM Provider**
   - OpenAI GPT-4 (best quality)
   - Anthropic Claude (large context)
   - Local models via Ollama (free, private)

2. **Create Analysis Routes**
   - Add API endpoints in `routes/bills.py`
   - Return LLM analysis results as JSON

3. **Build UI**
   - Show summaries on bill detail pages
   - Add "Analyze with AI" button
   - Display stakeholder impacts

4. **Automate**
   - Schedule nightly text fetching
   - Pre-generate summaries for popular bills
   - Cache LLM results in database

5. **Advanced Features**
   - Semantic search across bills
   - Compare similar bills
   - Track amendments over time
   - Generate plain language versions

## Documentation

- [Full LLM Guide](../development/bill-text-llm.md)
- [Bill Text Fetcher Service](../../services/bill_text_fetcher.py)
- [Fetch Script](../../fetch_bill_text.py)
- [Demo Script](../../demo_llm_processing.py)

## Troubleshooting

**No text extracted?**
- Check PDF URL is valid
- Ensure pdfplumber is installed
- Some PDFs may be scanned images

**Import errors?**
```bash
pip install pdfplumber PyPDF2
```

**Memory issues?**
- Use `--limit 10` to process fewer bills
- Process in batches
- Truncate text with `max_length`

**Token limits?**
- GPT-4: Use `max_length=6000` (~1500 tokens)
- Claude: Can handle full text (200k tokens)
- Local models: Typically 2k-4k tokens
