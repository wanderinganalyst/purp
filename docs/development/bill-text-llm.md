# Bill Text Fetching for LLM Processing

This document explains how to fetch and use full bill text for LLM processing in Purp.

## Overview

Purp can fetch full bill text from Missouri Legislature PDFs and store it in the database for:
- LLM-powered bill analysis
- Semantic search
- Automated summarization
- Impact analysis
- Plain language explanations

## Database Schema

The `bills` table includes:
- `full_text` (Text): Complete bill text extracted from PDFs
- `text_pdf_url` (String): URL to official bill text PDF
- `summary_pdf_url` (String): URL to bill summary PDF
- `text_fetched_at` (DateTime): When text was last fetched

## Fetching Bill Text

### Prerequisites

Install PDF parsing libraries:
```bash
source .venv/bin/activate
pip install pdfplumber PyPDF2
```

### Fetch Text for All Bills

```bash
python fetch_bill_text.py
```

### Fetch Specific Bills

```bash
python fetch_bill_text.py HB101 HB102 HB103
```

### Options

```bash
# Limit number of bills
python fetch_bill_text.py --limit 10

# Re-fetch bills that already have text
python fetch_bill_text.py --refetch

# Specify legislative year
python fetch_bill_text.py --year 2024
```

## Using Bill Text in Code

### Basic Retrieval

```python
from models import Bill

# Get bill with text
bill = Bill.query.filter_by(bill_number='HB101').first()

if bill.full_text:
    print(f"Bill text: {len(bill.full_text)} characters")
    print(bill.full_text[:500])  # First 500 chars
```

### LLM-Formatted Context

```python
# Get formatted text ready for LLM
llm_context = bill.get_llm_context()

# Limit context length (for token limits)
llm_context = bill.get_llm_context(max_length=4000)
```

### Extract Structured Sections

```python
from services.bill_text_fetcher import extract_key_sections

sections = extract_key_sections(bill.full_text)

# Available sections:
# - enacting_clause: "Be it enacted..." 
# - effective_date: When bill takes effect
# - numbered_sections: List of individual sections
```

### Search Bills by Content

```python
# Find bills mentioning specific terms
education_bills = Bill.query.filter(
    Bill.full_text.isnot(None),
    Bill.full_text.ilike('%education%')
).all()
```

## LLM Integration Examples

### OpenAI Example

```python
import openai
from models import Bill

bill = Bill.query.filter_by(bill_number='HB101').first()

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a legislative analyst."},
        {"role": "user", "content": f"Summarize this bill:\n\n{bill.get_llm_context(max_length=8000)}"}
    ]
)

summary = response.choices[0].message.content
```

### Anthropic Claude Example

```python
import anthropic
from models import Bill

client = anthropic.Anthropic(api_key="your-key")
bill = Bill.query.filter_by(bill_number='HB101').first()

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": f"Analyze this bill:\n\n{bill.get_llm_context()}"}
    ]
)

analysis = message.content[0].text
```

### Local Model Example (Ollama)

```python
import requests
from models import Bill

bill = Bill.query.filter_by(bill_number='HB101').first()

response = requests.post('http://localhost:11434/api/generate',
    json={
        "model": "llama2",
        "prompt": f"Summarize this bill:\n\n{bill.get_llm_context(max_length=4000)}"
    }
)

summary = response.json()['response']
```

## Analysis Use Cases

### 1. Bill Summarization

```python
from services.bill_text_fetcher import prepare_for_llm

bill_data = {
    'bill_number': bill.bill_number,
    'title': bill.title,
    'sponsor': bill.sponsor,
    'status': bill.status,
    'description': bill.description,
    'full_text': bill.full_text
}

# Create prompt for summarization
prompt = f"""Summarize this Missouri House Bill in 3-4 sentences for a general audience:

{prepare_for_llm(bill_data)}

Summary:"""
```

### 2. Impact Analysis

```python
prompt = f"""Analyze the potential impact of this bill on Missouri residents:

{bill.get_llm_context()}

Identify:
1. Who is affected
2. What changes
3. Potential benefits
4. Potential concerns"""
```

### 3. Stakeholder Identification

```python
prompt = f"""Identify stakeholders affected by this bill:

{bill.get_llm_context()}

For each stakeholder group, explain how they're impacted."""
```

### 4. Plain Language Translation

```python
prompt = f"""Explain this bill in simple terms that a high school student would understand:

{bill.get_llm_context()}

Avoid legal jargon and use clear, everyday language."""
```

### 5. Comparison Analysis

```python
bill1 = Bill.query.filter_by(bill_number='HB101').first()
bill2 = Bill.query.filter_by(bill_number='HB102').first()

prompt = f"""Compare these two bills:

BILL 1:
{bill1.get_llm_context(max_length=4000)}

BILL 2:
{bill2.get_llm_context(max_length=4000)}

How are they similar and different?"""
```

## Demo Script

Run the demo to see all features:

```bash
python demo_llm_processing.py
```

The demo shows:
1. Basic text retrieval
2. LLM formatting
3. Section extraction
4. Prompt generation
5. Batch processing
6. Content search

## API Endpoints (Future)

Consider adding these endpoints:

```python
# routes/bills.py

@bills_bp.route('/api/bills/<bill_number>/analyze', methods=['POST'])
def analyze_bill(bill_number):
    """Analyze bill with LLM."""
    bill = Bill.query.filter_by(bill_number=bill_number).first_or_404()
    
    analysis_type = request.json.get('type', 'summary')
    # Call LLM service
    # Return analysis
    
@bills_bp.route('/api/bills/<bill_number>/text', methods=['GET'])
def get_bill_text(bill_number):
    """Get full bill text."""
    bill = Bill.query.filter_by(bill_number=bill_number).first_or_404()
    return jsonify({
        'bill_number': bill.bill_number,
        'full_text': bill.full_text,
        'text_pdf_url': bill.text_pdf_url,
        'fetched_at': bill.text_fetched_at
    })
```

## Performance Considerations

### Text Storage
- Average bill: 5,000-15,000 words
- 100 bills: ~1-2 MB of text data
- Database TEXT columns handle this efficiently

### Fetching Strategy
- Fetch during off-peak hours
- Use background jobs (APScheduler)
- Cache PDF URLs to avoid re-parsing

### LLM Token Limits
- GPT-4: 8k-128k tokens (depending on model)
- Claude: 200k tokens
- Use `max_length` parameter to truncate

Example:
```python
# For GPT-4 (8k context)
context = bill.get_llm_context(max_length=6000)  # ~1500 tokens

# For Claude (200k context)
context = bill.get_llm_context()  # Full text
```

## Background Processing

Schedule text fetching:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from fetch_bill_text import fetch_text_for_bill

def scheduled_text_fetch():
    with app.app_context():
        # Fetch text for bills without it
        bills = Bill.query.filter(Bill.full_text.is_(None)).limit(10).all()
        for bill in bills:
            fetch_text_for_bill(bill)
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(
    scheduled_text_fetch,
    'cron',
    hour=2,  # 2 AM daily
    minute=0
)
```

## Troubleshooting

### No Text Extracted
- Check if PDF URL is valid
- Install pdfplumber: `pip install pdfplumber`
- Some PDFs may be scanned images (need OCR)

### Import Errors
```bash
pip install pdfplumber PyPDF2
```

### Database Migration
```bash
# Run migration to add columns
python init_db.py
```

### Memory Issues
- Process bills in batches
- Use `--limit` flag
- Increase available memory

## Next Steps

1. **Integrate LLM Service**: Choose OpenAI, Anthropic, or local model
2. **Create Analysis Routes**: Add API endpoints for bill analysis
3. **Build UI**: Display analysis results on bill detail pages
4. **Automate**: Schedule background text fetching and analysis
5. **Cache Results**: Store LLM analysis to avoid repeated API calls
6. **Export**: Allow downloading bill text in various formats

## Resources

- [Missouri Legislature Bill Search](https://house.mo.gov/billlist.aspx)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com)
- [Ollama (Local LLMs)](https://ollama.ai)
- [LangChain](https://python.langchain.com/) - LLM orchestration framework
