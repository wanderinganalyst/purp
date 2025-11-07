"""
AI Bill Drafting Service

This service helps representatives draft new bills using LLM analysis of:
- Previously PASSED bills (positive examples)
- Previously FAILED bills (negative examples - what to avoid)

The LLM learns from successful patterns and avoids failed approaches.
"""
from typing import List, Dict, Optional, Tuple
import json
from models import Bill, DraftBill, DraftBillComment, Representative, User
from extensions import db
from services.bill_text_fetcher import prepare_for_llm


# Bill status categorization
PASSED_STATUSES = [
    'signed',
    'enacted',
    'approved',
    'passed',
    'law',
    'effective',
    'adopted'
]

FAILED_STATUSES = [
    'defeated',
    'rejected',
    'vetoed',
    'failed',
    'withdrawn',
    'tabled',
    'postponed indefinitely'
]


def categorize_bill_status(status: str) -> str:
    """
    Categorize bill status as passed, failed, or active.
    
    Args:
        status: Bill status string
        
    Returns:
        'passed', 'failed', or 'active'
    """
    if not status:
        return 'active'
    
    status_lower = status.lower()
    
    for passed_status in PASSED_STATUSES:
        if passed_status in status_lower:
            return 'passed'
    
    for failed_status in FAILED_STATUSES:
        if failed_status in status_lower:
            return 'failed'
    
    return 'active'


def get_bills_by_category(topic: Optional[str] = None) -> Dict[str, List[Bill]]:
    """
    Get bills categorized by passed/failed status.
    
    Args:
        topic: Optional topic to filter bills (searches in title and description)
        
    Returns:
        Dict with 'passed' and 'failed' lists of bills
    """
    query = Bill.query.filter(Bill.full_text.isnot(None))
    
    if topic:
        topic_filter = f'%{topic}%'
        query = query.filter(
            (Bill.title.ilike(topic_filter)) |
            (Bill.description.ilike(topic_filter)) |
            (Bill.full_text.ilike(topic_filter))
        )
    
    bills = query.all()
    
    categorized = {
        'passed': [],
        'failed': [],
        'active': []
    }
    
    for bill in bills:
        category = categorize_bill_status(bill.status)
        categorized[category].append(bill)
    
    return categorized


def build_llm_training_context(
    passed_bills: List[Bill],
    failed_bills: List[Bill],
    max_examples: int = 5,
    max_length_per_bill: int = 2000
) -> str:
    """
    Build LLM context with passed bills (positive) and failed bills (negative).
    
    Args:
        passed_bills: List of successfully passed bills
        failed_bills: List of failed bills
        max_examples: Maximum examples to include from each category
        max_length_per_bill: Max characters per bill text
        
    Returns:
        Formatted context string for LLM
    """
    context = []
    
    # Header
    context.append("=" * 80)
    context.append("LEGISLATIVE ANALYSIS TRAINING DATA")
    context.append("=" * 80)
    context.append("")
    
    # Positive examples (passed bills)
    context.append("SUCCESSFUL BILLS (Passed/Signed into Law):")
    context.append("These bills were successfully enacted. Study their structure,")
    context.append("language, and approach as positive examples.")
    context.append("-" * 80)
    context.append("")
    
    for i, bill in enumerate(passed_bills[:max_examples], 1):
        context.append(f"POSITIVE EXAMPLE {i}:")
        context.append(f"Bill: {bill.bill_number}")
        context.append(f"Title: {bill.title or bill.description[:100]}")
        context.append(f"Status: {bill.status}")
        context.append(f"Sponsor: {bill.sponsor}")
        context.append("")
        
        if bill.full_text:
            text = bill.full_text[:max_length_per_bill]
            if len(bill.full_text) > max_length_per_bill:
                text += "\n... [truncated]"
            context.append(text)
        
        context.append("")
        context.append("-" * 80)
        context.append("")
    
    if not passed_bills:
        context.append("(No passed bills available for this topic)")
        context.append("")
    
    # Negative examples (failed bills)
    context.append("")
    context.append("FAILED BILLS (Defeated/Rejected):")
    context.append("These bills failed to pass. Identify what went wrong and")
    context.append("avoid similar patterns, language, or approaches.")
    context.append("-" * 80)
    context.append("")
    
    for i, bill in enumerate(failed_bills[:max_examples], 1):
        context.append(f"NEGATIVE EXAMPLE {i}:")
        context.append(f"Bill: {bill.bill_number}")
        context.append(f"Title: {bill.title or bill.description[:100]}")
        context.append(f"Status: {bill.status}")
        context.append(f"Sponsor: {bill.sponsor}")
        context.append("")
        
        if bill.full_text:
            text = bill.full_text[:max_length_per_bill]
            if len(bill.full_text) > max_length_per_bill:
                text += "\n... [truncated]"
            context.append(text)
        
        context.append("")
        context.append("-" * 80)
        context.append("")
    
    if not failed_bills:
        context.append("(No failed bills available for this topic)")
        context.append("")
    
    return '\n'.join(context)


def generate_bill_draft_prompt(
    topic: str,
    description: str,
    passed_bills: List[Bill],
    failed_bills: List[Bill],
    additional_instructions: Optional[str] = None
) -> str:
    """
    Generate a complete prompt for LLM to draft a new bill.
    
    Args:
        topic: Bill topic/subject
        description: What the bill should accomplish
        passed_bills: Successful bills to learn from
        failed_bills: Failed bills to avoid patterns from
        additional_instructions: Optional specific requirements
        
    Returns:
        Complete LLM prompt for bill drafting
    """
    training_context = build_llm_training_context(passed_bills, failed_bills)
    
    prompt = f"""{training_context}

{{"=" * 80}}
BILL DRAFTING REQUEST
{{"=" * 80}}

You are an expert legislative drafter for the Missouri House of Representatives.
Using the successful bills above as positive examples and the failed bills as
negative examples (what to avoid), draft a new bill on the following topic:

TOPIC: {topic}

OBJECTIVE: {description}
"""
    
    if additional_instructions:
        prompt += f"\nADDITIONAL REQUIREMENTS:\n{additional_instructions}\n"
    
    prompt += """

INSTRUCTIONS:
1. Study the SUCCESSFUL bills to understand what works:
   - Clear, concise language
   - Well-structured sections
   - Proper legal formatting
   - Effective enacting clauses
   - Realistic implementation timelines

2. Study the FAILED bills to understand what to avoid:
   - Overly complex language
   - Controversial provisions
   - Unclear objectives
   - Poor structure

3. Draft a complete bill that includes:
   - Bill title
   - Enacting clause ("Be it enacted by the General Assembly...")
   - Section A: Repeal/modification of existing statutes (if applicable)
   - Numbered sections with clear provisions
   - Effective date
   - Fiscal note considerations

4. Use Missouri legislative formatting standards
5. Keep language clear and professionally written
6. Ensure the bill is practical and implementable

DRAFT THE BILL BELOW:
"""
    
    return prompt


def analyze_bill_patterns(bills: List[Bill]) -> Dict[str, any]:
    """
    Analyze patterns in a set of bills for insights.
    
    Args:
        bills: List of bills to analyze
        
    Returns:
        Dict with pattern analysis
    """
    if not bills:
        return {
            'count': 0,
            'avg_length': 0,
            'common_sponsors': [],
            'common_words': []
        }
    
    from collections import Counter
    import re
    
    # Basic stats
    word_counts = [len(bill.full_text.split()) if bill.full_text else 0 for bill in bills]
    avg_length = sum(word_counts) / len(word_counts) if word_counts else 0
    
    # Common sponsors
    sponsors = [bill.sponsor for bill in bills if bill.sponsor]
    sponsor_counts = Counter(sponsors)
    common_sponsors = sponsor_counts.most_common(5)
    
    # Common words in successful bills
    all_text = ' '.join([bill.full_text for bill in bills if bill.full_text])
    words = re.findall(r'\b[a-z]{4,}\b', all_text.lower())
    word_counts = Counter(words)
    # Filter out common words
    stopwords = {'that', 'this', 'with', 'from', 'have', 'been', 'will', 'shall', 
                 'section', 'subsection', 'following', 'pursuant', 'thereof'}
    meaningful_words = {word: count for word, count in word_counts.items() 
                       if word not in stopwords}
    common_words = Counter(meaningful_words).most_common(10)
    
    return {
        'count': len(bills),
        'avg_length': int(avg_length),
        'common_sponsors': common_sponsors,
        'common_words': common_words
    }


def get_bill_drafting_statistics(topic: Optional[str] = None) -> Dict[str, any]:
    """
    Get statistics about bills for the bill drafting interface.
    
    Args:
        topic: Optional topic filter
        
    Returns:
        Dict with statistics
    """
    categorized = get_bills_by_category(topic)
    
    passed_analysis = analyze_bill_patterns(categorized['passed'])
    failed_analysis = analyze_bill_patterns(categorized['failed'])
    
    return {
        'topic': topic or 'All Topics',
        'passed': {
            'count': len(categorized['passed']),
            'bills': categorized['passed'][:5],  # Top 5 for preview
            'analysis': passed_analysis
        },
        'failed': {
            'count': len(categorized['failed']),
            'bills': categorized['failed'][:5],
            'analysis': failed_analysis
        },
        'active': {
            'count': len(categorized['active'])
        },
        'total_with_text': len(categorized['passed']) + len(categorized['failed']) + len(categorized['active'])
    }


def create_llm_bill_draft(
    topic: str,
    description: str,
    topic_filter: Optional[str] = None,
    additional_instructions: Optional[str] = None,
    max_examples: int = 3
) -> Tuple[str, Dict[str, any]]:
    """
    Create a bill draft using our custom TensorFlow model with passed/failed bill context.
    
    This is the main function to call from routes.
    
    Args:
        topic: Bill topic/title
        description: What the bill should accomplish
        topic_filter: Optional filter for similar bills
        additional_instructions: Optional specific requirements
        max_examples: Max number of example bills to include
        
    Returns:
        Tuple of (generated_bill, context_info)
        - generated_bill: Complete bill text generated by our AI
        - context_info: Dict with info about bills used as context
    """
    from services.bill_generator import get_bill_generator
    
    # Get categorized bills
    categorized = get_bills_by_category(topic_filter or topic)
    
    passed_bills = categorized['passed'][:max_examples]
    failed_bills = categorized['failed'][:max_examples]
    
    # Generate bill using our custom AI model
    generator = get_bill_generator()
    generated_bill = generator.generate_bill(
        topic=topic,
        description=description,
        passed_bills=passed_bills,
        failed_bills=failed_bills,
        additional_instructions=additional_instructions
    )
    
    # Get generation metadata
    metadata = generator.get_generation_metadata(passed_bills, failed_bills)
    
    # Context info for display
    context_info = {
        'passed_count': len(passed_bills),
        'failed_count': len(failed_bills),
        'passed_bills': [
            {
                'number': b.bill_number,
                'title': b.title or b.description[:100],
                'status': b.status
            } for b in passed_bills
        ],
        'failed_bills': [
            {
                'number': b.bill_number,
                'title': b.title or b.description[:100],
                'status': b.status
            } for b in failed_bills
        ],
        'topic_filter': topic_filter or topic,
        'model_info': metadata
    }
    
    return generated_bill, context_info


# ============================================================================
# DRAFT BILL MANAGEMENT
# ============================================================================

def save_draft_bill(
    representative_id: int,
    title: str,
    content: str,
    description: Optional[str] = None,
    visibility: str = 'hidden',
    topic: Optional[str] = None,
    llm_prompt_used: Optional[str] = None,
    based_on_bills: Optional[List[str]] = None
) -> DraftBill:
    """
    Save a new draft bill.
    
    Args:
        representative_id: ID of the representative creating the draft
        title: Bill title
        content: Bill text/content
        description: Optional description
        visibility: 'hidden', 'constituents', or 'public'
        topic: Optional topic tag
        llm_prompt_used: Optional LLM prompt that generated this
        based_on_bills: Optional list of bill_numbers used as examples
        
    Returns:
        The created DraftBill object
    """
    draft = DraftBill(
        representative_id=representative_id,
        title=title,
        content=content,
        description=description,
        visibility=visibility,
        topic=topic,
        llm_prompt_used=llm_prompt_used,
        based_on_bills=json.dumps(based_on_bills) if based_on_bills else None
    )
    
    db.session.add(draft)
    db.session.commit()
    
    return draft


def update_draft_bill(
    draft_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    description: Optional[str] = None,
    visibility: Optional[str] = None
) -> Optional[DraftBill]:
    """
    Update an existing draft bill.
    
    Args:
        draft_id: ID of the draft bill
        title: Optional new title
        content: Optional new content
        description: Optional new description
        visibility: Optional new visibility setting
        
    Returns:
        Updated DraftBill or None if not found
    """
    draft = DraftBill.query.get(draft_id)
    if not draft:
        return None
    
    if title is not None:
        draft.title = title
    if content is not None:
        draft.content = content
    if description is not None:
        draft.description = description
    if visibility is not None:
        if visibility not in ['hidden', 'constituents', 'public']:
            raise ValueError(f"Invalid visibility: {visibility}")
        draft.visibility = visibility
    
    db.session.commit()
    return draft


def update_draft_visibility(draft_id: int, visibility: str) -> Optional[DraftBill]:
    """
    Update just the visibility of a draft bill.
    
    Args:
        draft_id: ID of the draft bill
        visibility: 'hidden', 'constituents', or 'public'
        
    Returns:
        Updated DraftBill or None if not found
    """
    return update_draft_bill(draft_id, visibility=visibility)


def get_rep_drafts(representative_id: int) -> List[DraftBill]:
    """
    Get all draft bills for a specific representative.
    
    Args:
        representative_id: ID of the representative
        
    Returns:
        List of DraftBill objects ordered by most recent
    """
    return DraftBill.query.filter_by(
        representative_id=representative_id
    ).order_by(
        DraftBill.updated_at.desc()
    ).all()


def get_visible_drafts_for_user(user: User, representative_id: Optional[int] = None) -> List[DraftBill]:
    """
    Get draft bills visible to a specific user.
    
    Args:
        user: User object
        representative_id: Optional filter to specific representative
        
    Returns:
        List of visible DraftBill objects
    """
    query = DraftBill.query
    
    if representative_id:
        query = query.filter_by(representative_id=representative_id)
    
    # Get all drafts and filter by visibility rules
    all_drafts = query.order_by(DraftBill.updated_at.desc()).all()
    
    visible_drafts = []
    for draft in all_drafts:
        if draft.can_view(user):
            visible_drafts.append(draft)
    
    return visible_drafts


def get_draft_by_id(draft_id: int) -> Optional[DraftBill]:
    """Get a draft bill by ID."""
    return DraftBill.query.get(draft_id)


def delete_draft_bill(draft_id: int) -> bool:
    """
    Delete a draft bill.
    
    Args:
        draft_id: ID of the draft bill
        
    Returns:
        True if deleted, False if not found
    """
    draft = DraftBill.query.get(draft_id)
    if not draft:
        return False
    
    db.session.delete(draft)
    db.session.commit()
    return True


def add_draft_comment(
    draft_bill_id: int,
    user_id: int,
    comment_text: str,
    is_staffer: bool = False
) -> Optional[DraftBillComment]:
    """
    Add a comment to a draft bill.
    
    Args:
        draft_bill_id: ID of the draft bill
        user_id: ID of the commenting user
        comment_text: Comment text
        is_staffer: True if comment is from a staffer
        
    Returns:
        Created DraftBillComment or None if draft not found
    """
    draft = DraftBill.query.get(draft_bill_id)
    if not draft:
        return None
    
    comment = DraftBillComment(
        draft_bill_id=draft_bill_id,
        user_id=user_id,
        comment_text=comment_text,
        is_staffer=is_staffer
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return comment


def get_draft_comments(draft_bill_id: int) -> List[DraftBillComment]:
    """
    Get all comments for a draft bill.
    
    Args:
        draft_bill_id: ID of the draft bill
        
    Returns:
        List of DraftBillComment objects ordered by creation time
    """
    return DraftBillComment.query.filter_by(
        draft_bill_id=draft_bill_id
    ).order_by(
        DraftBillComment.created_at.asc()
    ).all()


def get_draft_statistics(representative_id: int) -> Dict:
    """
    Get statistics about a representative's draft bills.
    
    Args:
        representative_id: ID of the representative
        
    Returns:
        Dict with counts and stats
    """
    drafts = get_rep_drafts(representative_id)
    
    stats = {
        'total_drafts': len(drafts),
        'hidden_count': sum(1 for d in drafts if d.visibility == 'hidden'),
        'constituents_count': sum(1 for d in drafts if d.visibility == 'constituents'),
        'public_count': sum(1 for d in drafts if d.visibility == 'public'),
        'total_comments': sum(d.comments.count() for d in drafts),
        'recent_drafts': drafts[:5]  # 5 most recent
    }
    
    return stats

