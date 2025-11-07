# AI Bill Drafting Feature

## Overview

The AI Bill Drafting feature is an exclusive tool for representatives that leverages machine learning to help draft new legislation. It analyzes previously passed bills (positive examples) and failed bills (negative examples) to generate intelligent prompts for LLM-based bill drafting.

## How It Works

### 1. Learning from History
The system analyzes Missouri's legislative history:
- **Passed Bills** ✓ - Bills that were signed into law serve as positive examples of effective legislation
- **Failed Bills** ✗ - Bills that were defeated or rejected highlight patterns to avoid

### 2. AI-Powered Drafting
Representatives provide:
- Bill topic/title
- Objective and description
- Optional topic filter for similar bills
- Additional requirements

The system generates a comprehensive LLM prompt that includes:
- Full text of successful bills for reference
- Full text of failed bills to avoid their patterns
- Structured instructions for drafting
- Missouri legislative formatting standards

### 3. LLM Integration
The generated prompt can be used with:
- **ChatGPT** (OpenAI)
- **Claude** (Anthropic)
- **Local LLMs** (Ollama)

## Features

### Main Drafting Interface
- **Path**: `/draft-bill`
- **Access**: Representatives only
- **Features**:
  - Form to specify bill details
  - Real-time statistics on available examples
  - Preview of successful and failed bills
  - Customizable number of example bills (2-5)

### Statistics Dashboard
- **Path**: `/draft-bill/statistics`
- **Shows**:
  - Total passed/failed/active bills
  - Common sponsors by category
  - Most frequent topics and keywords
  - Average bill length comparison
  - Success rate analysis

### Example Browser
- **Path**: `/draft-bill/browse`
- **Features**:
  - Browse bills by category (passed/failed/active)
  - Filter by topic
  - View full bill details
  - Links to bill detail pages

### Result Page
- **Displays**:
  - Generated LLM prompt
  - Context information (which bills were used)
  - Copy-to-clipboard functionality
  - Direct links to ChatGPT and Claude
  - Step-by-step usage instructions

## Database Schema

Bills are categorized based on their status:

### Passed Bills (Positive Examples)
Statuses include:
- "signed"
- "enacted"
- "approved"
- "passed"
- "law"
- "effective"
- "adopted"

### Failed Bills (Negative Examples)
Statuses include:
- "defeated"
- "rejected"
- "vetoed"
- "failed"
- "withdrawn"
- "tabled"
- "postponed indefinitely"

### Active Bills
All other statuses (pending, in committee, etc.)

## Services

### `services/bill_drafting.py`

Main service file with functions:

#### `categorize_bill_status(status: str) -> str`
Categorizes a bill as 'passed', 'failed', or 'active'

#### `get_bills_by_category(topic: Optional[str]) -> Dict`
Returns bills organized by category, optionally filtered by topic

#### `build_llm_training_context(...) -> str`
Builds the training context with passed and failed bill examples

#### `generate_bill_draft_prompt(...) -> str`
Creates complete LLM prompt for bill drafting

#### `analyze_bill_patterns(bills: List[Bill]) -> Dict`
Analyzes patterns in bills (common sponsors, words, length)

#### `get_bill_drafting_statistics(...) -> Dict`
Returns statistics for the drafting interface

#### `create_llm_bill_draft(...) -> Tuple[str, Dict]`
Main function that generates prompt and context info

## Routes

### `routes/bill_drafting.py`

All routes require representative role (`@rep_required` decorator):

- `GET /draft-bill` - Main drafting interface
- `POST /draft-bill/generate` - Generate bill draft prompt
- `POST /draft-bill/api/generate` - API endpoint (returns JSON)
- `GET /draft-bill/statistics` - Statistics dashboard
- `GET /draft-bill/api/statistics` - API endpoint for stats
- `GET /draft-bill/browse` - Browse example bills

## Templates

### `templates/bill_drafting/draft.html`
- Main interface with form
- Statistics cards
- Preview of passed/failed bills
- Topic filter

### `templates/bill_drafting/result.html`
- Shows generated prompt
- Context information
- Copy-to-clipboard button
- Usage instructions
- Links to LLM services

### `templates/bill_drafting/browse.html`
- Category tabs (passed/failed/active)
- Topic filter
- Bill cards with details

### `templates/bill_drafting/statistics.html`
- Overall statistics
- Passed bills analysis
- Failed bills analysis
- Key insights

## Usage Example

### For Representatives:

1. **Navigate** to "AI Bill Drafting" in the menu

2. **Fill out the form**:
   ```
   Topic: Education Funding Reform
   Description: Increase funding for public schools in rural districts
   Topic Filter: education
   Max Examples: 3
   ```

3. **Click** "Generate Bill Draft Prompt"

4. **Copy** the generated prompt

5. **Paste** into ChatGPT or Claude:
   - The prompt includes 3 successful education bills
   - And 3 failed education bills
   - Plus specific instructions for drafting

6. **Review** the AI-generated bill

7. **Refine** by asking the LLM:
   - "Make the language more concise"
   - "Add a fiscal impact section"
   - "Revise the effective date"

8. **Legal Review** before introduction

## Sample Generated Prompt Structure

```
================================================================================
LEGISLATIVE ANALYSIS TRAINING DATA
================================================================================

SUCCESSFUL BILLS (Passed/Signed into Law):
These bills were successfully enacted...

POSITIVE EXAMPLE 1:
Bill: HB123
Title: Rural Education Funding Act
Status: Signed by Governor
...full text...

FAILED BILLS (Defeated/Rejected):
These bills failed to pass...

NEGATIVE EXAMPLE 1:
Bill: HB456
Title: Education Funding Overhaul
Status: Defeated
...full text...

================================================================================
BILL DRAFTING REQUEST
================================================================================

TOPIC: Education Funding Reform
OBJECTIVE: Increase funding for public schools in rural districts

INSTRUCTIONS:
1. Study the SUCCESSFUL bills to understand what works...
2. Study the FAILED bills to understand what to avoid...
3. Draft a complete bill that includes...

DRAFT THE BILL BELOW:
```

## Setup

### 1. Install Dependencies
```bash
pip install pdfplumber PyPDF2
```

### 2. Fetch Bill Text
```bash
python fetch_bill_text.py
```

### 3. Update Bill Statuses (for demo)
```bash
python update_bill_statuses.py
```

### 4. Access Feature
- Login as a representative
- Navigate to "AI Bill Drafting"

## API Usage

### Generate Draft (JSON)
```bash
POST /draft-bill/api/generate
Content-Type: application/json

{
  "topic": "Education Funding Reform",
  "description": "Increase funding for rural schools",
  "topic_filter": "education",
  "max_examples": 3
}
```

Response:
```json
{
  "success": true,
  "prompt": "...complete LLM prompt...",
  "context": {
    "passed_count": 3,
    "failed_count": 3,
    "passed_bills": [...],
    "failed_bills": [...]
  }
}
```

### Get Statistics (JSON)
```bash
GET /draft-bill/api/statistics?topic=education
```

Response:
```json
{
  "topic": "education",
  "passed": {
    "count": 5,
    "bills": [...],
    "analysis": {...}
  },
  "failed": {
    "count": 3,
    "bills": [...],
    "analysis": {...}
  },
  "total_with_text": 100
}
```

## Security

- **Role-based access**: Only representatives can access this feature
- **Session validation**: All routes check for valid rep session
- **Input validation**: Form data is validated before processing
- **SQL injection protection**: Using SQLAlchemy ORM

## Best Practices

### For Representatives:
1. **Be specific** in your bill description
2. **Use topic filters** to find relevant examples
3. **Start with 3 examples** (balanced context vs. length)
4. **Always review** AI-generated content
5. **Get legal review** before introduction

### For AI prompts:
1. The more context, the better the results
2. Include specific requirements in additional instructions
3. Iterate - ask the LLM for revisions
4. Compare outputs from multiple LLMs

## Limitations

- **Requires bill text**: Bills must have full_text populated
- **Status accuracy**: Depends on accurate bill status data
- **LLM access**: Representatives need their own LLM accounts
- **Not legal advice**: AI output requires human review

## Future Enhancements

1. **Direct LLM integration**: Call APIs directly from Purp
2. **Save drafts**: Store generated bills in database
3. **Version control**: Track revisions and amendments
4. **Collaboration**: Share drafts with other representatives
5. **Analysis tools**: Automated bill impact analysis
6. **Fine-tuning**: Custom model trained on Missouri legislation

## Troubleshooting

### No bills showing up?
```bash
python fetch_bill_text.py --limit 10
python update_bill_statuses.py
```

### Need more examples?
```bash
python fetch_bill_text.py  # Fetch all bills
```

### LLM prompt too long?
- Reduce `max_examples` to 2
- Use more specific topic filters
- The service automatically truncates each bill to 2000 chars

## Files

- `services/bill_drafting.py` - Core service (400 lines)
- `routes/bill_drafting.py` - Web routes (180 lines)
- `templates/bill_drafting/*.html` - UI templates (800 lines)
- `update_bill_statuses.py` - Demo status updater
- `docs/features/bill-drafting.md` - This file

## Success! ✓

Representatives can now:
- ✅ Access AI-powered bill drafting
- ✅ Learn from passed bills
- ✅ Avoid failed bill patterns
- ✅ Generate LLM prompts
- ✅ Browse example legislation
- ✅ View detailed statistics
