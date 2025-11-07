# Draft Bill Workspace Feature

## Overview

The Draft Bill Workspace allows representatives to manage AI-generated bill drafts, control their visibility, and receive feedback from constituents and staff.

## Features

### For Representatives
- **AI Bill Drafting**: Generate bill drafts using LLM with positive/negative learning from past bills
- **Draft Workspace**: Central hub to manage all draft bills
- **Visibility Controls**: Three visibility levels for each draft
  - 🔒 **Hidden**: Only you and your staff can see
  - 👥 **Constituents**: Your constituents can see and comment
  - 🌎 **Public**: Everyone can see and comment
- **Save Drafts**: Save AI-generated bills directly from the result page
- **Edit & Update**: Modify draft bills and their visibility settings
- **Delete Drafts**: Remove drafts you no longer need

### For Staff
- **Shared Workspace**: Access your representative's draft bills
- **Internal Comments**: Add staff-only notes and feedback
- **Collaboration**: Help refine bills before public release

### For Constituents
- **View Drafts**: See bills your representative is working on
- **Provide Feedback**: Comment on drafts marked for constituent visibility
- **Track Progress**: See updates as drafts evolve

### For Everyone
- **Public Drafts**: View and comment on publicly-shared draft bills
- **Representative Transparency**: See what your reps are working on

## User Roles

### Representative (`role='rep'`)
- Full access to all features
- Can create, edit, and delete draft bills
- Can control visibility of their drafts
- Can see all comments (including staff comments)

### Staffer (`role='staffer'`)
- Access to their representative's drafts
- Can view all drafts (including hidden ones)
- Can add internal comments marked as "staff"
- Cannot change visibility or delete drafts

### Regular Users
- Can view public and constituent-visible drafts
- Can comment on visible drafts
- Constituent status determined by `representative_district` field

## Database Schema

### DraftBill Model
```python
- id: Primary key
- representative_id: Foreign key to representatives table
- title: Bill title
- description: Optional description
- content: Full bill text
- visibility: 'hidden', 'constituents', or 'public'
- topic: Optional topic tag
- llm_prompt_used: Optional LLM prompt that generated this
- based_on_bills: Optional JSON list of example bills used
- created_at: Timestamp
- updated_at: Timestamp
```

### DraftBillComment Model
```python
- id: Primary key
- draft_bill_id: Foreign key to draft_bills table
- user_id: Foreign key to users table
- comment_text: Comment content
- is_staffer: Boolean (True for staff comments)
- created_at: Timestamp
- updated_at: Timestamp
```

### User Model Updates
```python
- rep_boss_id: Foreign key to representatives (for staffers)
- role: Extended to include 'staffer' option
```

## Routes

### Workspace Routes
- `GET /draft-bill/workspace` - Representative's draft workspace
- `POST /draft-bill/save` - Save a new draft bill
- `GET /draft-bill/<id>` - View draft bill details
- `POST /draft-bill/<id>/visibility` - Update visibility
- `POST /draft-bill/<id>/comment` - Add comment
- `POST /draft-bill/<id>/delete` - Delete draft bill

### Existing Routes Enhanced
- `POST /draft-bill/generate` - Now includes "Save as Draft" form
- Representative profile pages - Show visible drafts

## Visibility Rules

### Hidden Drafts
- ✅ Representative (owner)
- ✅ Staff of the representative
- ❌ Constituents
- ❌ Public

### Constituent Drafts
- ✅ Representative (owner)
- ✅ Staff of the representative
- ✅ Constituents (users with matching `representative_district`)
- ❌ Non-constituents

### Public Drafts
- ✅ Everyone (including anonymous users)

## Workflow

### 1. Create Draft from AI Generation
1. Rep uses AI Bill Drafting tool
2. Generates LLM prompt with passed/failed bill examples
3. Copies prompt to ChatGPT/Claude
4. Receives AI-generated bill text
5. Pastes bill into "Save as Draft" form on result page
6. Chooses visibility level
7. Saves draft to workspace

### 2. Manage Draft in Workspace
1. Rep visits `/draft-bill/workspace`
2. Sees all drafts with statistics
3. Can click on any draft to view/edit
4. Can change visibility with dropdown
5. Can delete unwanted drafts

### 3. Get Feedback
1. Rep sets draft to 'constituents' or 'public'
2. Constituents see draft on rep's profile page
3. Users click "View & Comment" to see full draft
4. Users post comments with feedback
5. Staff can add internal notes marked as "staff"
6. Rep reviews all feedback

### 4. Publish or Revise
1. Rep reviews comments
2. Makes revisions as needed
3. Can save updated versions
4. Eventually introduces as actual legislation

## Templates

### `workspace.html`
- Main workspace dashboard
- Statistics cards (total, hidden, constituent, public)
- Table of all drafts with inline visibility controls
- Quick actions (view, delete)
- Empty state for new users

### `draft_detail.html`
- Full draft bill display
- Metadata (title, description, topic, dates)
- Bill content with copy button
- AI generation details (for owner)
- Comments section with form
- Visibility controls (for owner)
- Delete option (for owner)

### `result.html` (enhanced)
- Original LLM prompt display
- **New**: "Save as Draft" form
- Pre-filled with topic/description
- Textarea for pasting AI-generated content
- Visibility selector
- Direct save to workspace

### `rep_detail.html` (enhanced)
- **New**: "Bills in Development" section
- Shows visible draft bills
- Filtered by user's permissions
- Cards with title, description, topic, comment count
- "View & Comment" button

## Service Layer

### `services/bill_drafting.py`

#### Draft Management Functions
- `save_draft_bill()` - Create new draft
- `update_draft_bill()` - Update existing draft
- `update_draft_visibility()` - Change visibility setting
- `get_rep_drafts()` - Get all drafts for a representative
- `get_visible_drafts_for_user()` - Get drafts visible to specific user
- `get_draft_by_id()` - Get single draft
- `delete_draft_bill()` - Remove draft
- `add_draft_comment()` - Add comment to draft
- `get_draft_comments()` - Get all comments for draft
- `get_draft_statistics()` - Get counts and stats

## Navigation Updates

### Sidebar (for Representatives)
```
Bills
├─ All Bills
├─ AI Bill Drafting
└─ Draft Workspace ← NEW
```

### Sidebar (for Staffers)
```
Bills
├─ All Bills
└─ Draft Workspace ← NEW
```

## Testing

### Test Users Created
Run `test_draft_workspace.py` to create test users:

- **testrep** (password: test123)
  - Role: Representative
  - District: 001
  - Can create and manage drafts

- **teststaffer** (password: test123)
  - Role: Staffer
  - Works for: District 001 rep
  - Can view all drafts and add staff comments

- **testconstituent** (password: test123)
  - Role: Regular user
  - District: 001 (same as rep)
  - Can see constituent and public drafts

- **testnonconstituent** (password: test123)
  - Role: Regular user
  - District: 002 (different from rep)
  - Can only see public drafts

### Test Data Created
- 3 draft bills with different visibility levels
- 3 comments demonstrating different user types
- Visibility updates demonstrated

## Security Considerations

### Access Control
- Decorators enforce role requirements (`@rep_required`, `@rep_or_staffer_required`)
- `DraftBill.can_view()` method implements visibility logic
- Session-based authentication required for all actions
- Database-level foreign key constraints

### Data Validation
- Required fields enforced (title, content)
- Visibility must be one of: 'hidden', 'constituents', 'public'
- User ownership verified before updates/deletes
- SQL injection prevented by SQLAlchemy ORM

### Privacy
- Hidden drafts never exposed in API or templates
- Constituent filtering based on district matching
- Staff comments clearly marked
- LLM prompts only visible to draft owner

## Performance Considerations

- Draft queries filtered by representative_id (indexed)
- Comments loaded with drafts via relationship
- Visibility checks done in Python (cached in memory)
- No N+1 queries with proper eager loading

## Future Enhancements

### Potential Features
1. **Draft Versions**: Track revision history
2. **Collaboration**: Multiple reps co-authoring
3. **Bill Introduction**: Direct submit to legislative system
4. **Email Notifications**: Alert constituents of new drafts
5. **Rich Text Editor**: Better formatting for bill content
6. **PDF Export**: Generate formatted PDF versions
7. **Analytics**: Track engagement metrics
8. **Tags**: Better organization with multiple tags
9. **Search**: Full-text search across drafts
10. **API**: RESTful API for third-party integrations

## Troubleshooting

### Draft Not Visible
- Check visibility setting
- Verify user's district matches (for constituent visibility)
- Ensure user is logged in
- Check `DraftBill.can_view()` logic

### Cannot Save Draft
- Verify user has `representative_id` set
- Check required fields (title, content)
- Ensure database tables exist (run migration)
- Check server logs for errors

### Comments Not Appearing
- Verify draft is visible to user
- Check comment was saved (database query)
- Refresh page to reload comments
- Check user permissions

## Files Modified/Created

### Models
- `models/__init__.py` - Added DraftBill, DraftBillComment, User.rep_boss_id

### Services
- `services/bill_drafting.py` - Added 12 draft management functions

### Routes
- `routes/bill_drafting.py` - Added 7 new routes for workspace
- `routes/representatives.py` - Added draft_bills query

### Templates
- `templates/bill_drafting/workspace.html` - NEW
- `templates/bill_drafting/draft_detail.html` - NEW
- `templates/bill_drafting/result.html` - Enhanced with save form
- `templates/rep_detail.html` - Added draft bills section
- `templates/base.html` - Added navigation links

### Migrations
- `migrations/versions/add_draft_bills_and_staffers.py` - Database schema

### Tests
- `test_draft_workspace.py` - Comprehensive test suite

## Summary

This feature provides a complete workflow for representatives to:
1. Generate bill drafts using AI
2. Save and manage drafts in a workspace
3. Control who can see each draft
4. Receive feedback from constituents and staff
5. Iterate on drafts before formal introduction

The system enforces proper access control, provides transparency when desired, and facilitates collaboration between representatives, staff, and constituents.
