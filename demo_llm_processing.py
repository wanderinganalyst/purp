#!/usr/bin/env python3
"""
Demo script showing how to use bill text data for LLM processing.

This demonstrates:
1. Querying bills with full text
2. Preparing text for LLM input
3. Extracting structured sections
4. Generating prompts for analysis
"""
from models import Bill
from services.bill_text_fetcher import extract_key_sections, prepare_for_llm
from main import app


def demo_basic_retrieval():
    """Demo: Basic bill text retrieval."""
    print("=" * 80)
    print("DEMO 1: Basic Bill Text Retrieval")
    print("=" * 80)
    print()
    
    with app.app_context():
        # Get first bill with text
        bill = Bill.query.filter(Bill.full_text.isnot(None)).first()
        
        if not bill:
            print("No bills with full text found. Run fetch_bill_text.py first.")
            return
        
        print(f"Bill: {bill.bill_number}")
        print(f"Title: {bill.title}")
        print(f"Sponsor: {bill.sponsor}")
        print(f"Text length: {len(bill.full_text)} characters")
        print(f"Word count: {len(bill.full_text.split())} words")
        print()
        print("First 500 characters:")
        print("-" * 80)
        print(bill.full_text[:500])
        print("-" * 80)
        print()


def demo_llm_formatting():
    """Demo: Format bill for LLM processing."""
    print("=" * 80)
    print("DEMO 2: LLM-Ready Formatting")
    print("=" * 80)
    print()
    
    with app.app_context():
        bill = Bill.query.filter(Bill.full_text.isnot(None)).first()
        
        if not bill:
            print("No bills with full text found.")
            return
        
        # Get LLM context (limited to 2000 chars for display)
        llm_context = bill.get_llm_context(max_length=2000)
        
        print("Formatted for LLM:")
        print(llm_context)
        print()


def demo_section_extraction():
    """Demo: Extract structured sections from bill text."""
    print("=" * 80)
    print("DEMO 3: Section Extraction")
    print("=" * 80)
    print()
    
    with app.app_context():
        bill = Bill.query.filter(Bill.full_text.isnot(None)).first()
        
        if not bill:
            print("No bills with full text found.")
            return
        
        sections = extract_key_sections(bill.full_text)
        
        print(f"Analyzing {bill.bill_number}...")
        print()
        
        if sections.get('enacting_clause'):
            print("Enacting Clause:")
            print(sections['enacting_clause'])
            print()
        
        if sections.get('effective_date'):
            print("Effective Date:")
            print(sections['effective_date'])
            print()
        
        if sections.get('numbered_sections'):
            print(f"Found {len(sections['numbered_sections'])} numbered sections:")
            for i, section in enumerate(sections['numbered_sections'][:3], 1):
                # Show first 200 chars of each section
                preview = section[:200].replace('\n', ' ')
                print(f"  {i}. {preview}...")
            print()


def demo_llm_prompts():
    """Demo: Generate prompts for LLM analysis."""
    print("=" * 80)
    print("DEMO 4: LLM Analysis Prompts")
    print("=" * 80)
    print()
    
    with app.app_context():
        bill = Bill.query.filter(Bill.full_text.isnot(None)).first()
        
        if not bill:
            print("No bills with full text found.")
            return
        
        # Example prompts for different analysis tasks
        prompts = {
            "Summary": f"""Summarize the following Missouri House Bill in 2-3 sentences:

{bill.get_llm_context(max_length=4000)}

Summary:""",
            
            "Impact Analysis": f"""Analyze the potential impact of this bill on Missouri residents:

{bill.get_llm_context(max_length=4000)}

What are the key impacts?""",
            
            "Stakeholder Analysis": f"""Identify the main stakeholders affected by this bill:

{bill.get_llm_context(max_length=4000)}

List the stakeholders and how they're affected:""",
            
            "Plain Language": f"""Explain this bill in plain language for a general audience:

{bill.get_llm_context(max_length=4000)}

Plain language explanation:""",
        }
        
        for task, prompt in prompts.items():
            print(f"\n--- {task} Prompt ---")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print()


def demo_batch_analysis():
    """Demo: Batch processing for multiple bills."""
    print("=" * 80)
    print("DEMO 5: Batch Analysis")
    print("=" * 80)
    print()
    
    with app.app_context():
        bills = Bill.query.filter(Bill.full_text.isnot(None)).limit(5).all()
        
        if not bills:
            print("No bills with full text found.")
            return
        
        print(f"Processing {len(bills)} bills for batch analysis...")
        print()
        
        for bill in bills:
            word_count = len(bill.full_text.split())
            sections = extract_key_sections(bill.full_text)
            
            print(f"{bill.bill_number}")
            print(f"  Sponsor: {bill.sponsor}")
            print(f"  Words: {word_count:,}")
            print(f"  Sections: {len(sections.get('numbered_sections', []))}")
            print(f"  Has enacting clause: {bool(sections.get('enacting_clause'))}")
            print(f"  Has effective date: {bool(sections.get('effective_date'))}")
            print()


def demo_search_in_text():
    """Demo: Search for specific terms in bill text."""
    print("=" * 80)
    print("DEMO 6: Text Search")
    print("=" * 80)
    print()
    
    search_terms = ['education', 'tax', 'healthcare', 'budget']
    
    with app.app_context():
        for term in search_terms:
            # Case-insensitive search
            bills = Bill.query.filter(
                Bill.full_text.isnot(None),
                Bill.full_text.ilike(f'%{term}%')
            ).all()
            
            print(f"'{term}': {len(bills)} bills")
            
            if bills:
                # Show first 3
                for bill in bills[:3]:
                    print(f"  - {bill.bill_number}: {bill.title[:60]}...")
            print()


def main():
    """Run all demos."""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  PURP Bill Text LLM Processing Demo".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")
    
    demos = [
        demo_basic_retrieval,
        demo_llm_formatting,
        demo_section_extraction,
        demo_llm_prompts,
        demo_batch_analysis,
        demo_search_in_text,
    ]
    
    for demo in demos:
        try:
            demo()
            input("\nPress Enter to continue to next demo...")
            print("\n")
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"\n✗ Error in demo: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Integrate with your LLM of choice (OpenAI, Anthropic, local models)")
    print("  2. Build analysis endpoints in routes/")
    print("  3. Create UI for bill analysis results")
    print("  4. Set up background jobs for automated analysis")
    print()


if __name__ == '__main__':
    main()
