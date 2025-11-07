# Admin Access to Representative Features

## Overview
Admin users now have full access to all representative features, including the AI Bill Drafting and Draft Workspace functionality. This allows administrators to oversee and manage draft bills for all representatives in the system.

## Changes Made

### 1. Updated Access Control Decorators
**File:** `routes/bill_drafting.py`

#### `@rep_required` Decorator
- **Before:** Only allowed users with `role == 'rep'`
- **After:** Allows users with `role in ['rep', 'admin']`
- **Impact:** Admin users can now access all rep-only routes

#### `@rep_or_staffer_required` Decorator
- **Before:** Only allowed users with `role in ['rep', 'staffer']`
- **After:** Allows users with `role in ['rep', 'staffer', 'admin']`
- **Impact:** Admin users can access routes meant for reps and their staff

### 2. Workspace Route Enhancement
**File:** `routes/bill_drafting.py` - `workspace()` function

**Admin-Specific Features:**
- Admin can view any representative's draft workspace
- Uses `?rep_id=X` query parameter to select which representative's drafts to view
- Defaults to first representative if no `rep_id` specified
- Passes `all_reps` list to template for dropdown selector
- Maintains same statistics and draft viewing as regular reps

**Code Addition:**
```python
elif user.role == 'admin':
    # Admin can view any representative's workspace
    rep_id = request.args.get('rep_id', type=int)
    
    if rep_id:
        representative = Representative.query.get(rep_id)
    else:
        # Default to first representative
        representative = Representative.query.order_by(Representative.district).first()
    
    # Get all reps for dropdown selector
    all_reps = Representative.query.order_by(Representative.district).all()
```

### 3. Save Draft Route Updates
**File:** `routes/bill_drafting.py` - `save_draft()` function

**Admin Capabilities:**
- Admin can save drafts for any representative
- Requires `rep_id` form parameter when admin saves
- Validates representative exists before saving
- Error handling for missing/invalid representative

**Logic Flow for Admin:**
1. Check if user is admin
2. Get `rep_id` from form data
3. Validate representative exists
4. Use that representative's ID for draft creation

### 4. Permission Updates for Other Routes

#### `update_visibility()` Route
- **Before:** Only draft creator could update visibility
- **After:** Draft creator OR admin can update visibility
- **Check:** `if user.role != 'admin' and draft.representative_id != user.representative_id`

#### `view_draft()` Route
- **Before:** Only owner or staffer could edit
- **After:** Owner, staffer, OR admin can edit
- **Added:** `is_admin = user and user.role == 'admin'`
- **Updated:** `can_edit = is_owner or is_staffer or is_admin`

#### `delete_draft()` Route
- **Before:** Only draft creator could delete
- **After:** Draft creator OR admin can delete
- **Check:** `if user.role != 'admin' and draft.representative_id != user.representative_id`

### 5. Navigation Updates
**File:** `templates/base.html`

**Change:**
```html
<!-- Before -->
{% if session.get('role') == 'rep' %}
<a class="nav-link" href="{{ url_for('bill_drafting.draft_bill') }}">
    <i class="bi bi-robot"></i> AI Bill Drafting
</a>

<!-- After -->
{% if session.get('role') in ['rep', 'admin'] %}
<a class="nav-link" href="{{ url_for('bill_drafting.draft_bill') }}">
    <i class="bi bi-robot"></i> AI Bill Drafting
</a>
```

**Result:** Admin users now see "AI Bill Drafting" and "Draft Workspace" links in sidebar

### 6. Workspace Template Enhancement
**File:** `templates/bill_drafting/workspace.html`

**Added Representative Selector for Admin:**
```html
{% if user.role == 'admin' and all_reps %}
<div class="me-3 d-inline-block">
    <label for="repSelector" class="form-label mb-0 me-2">Representative:</label>
    <select id="repSelector" class="form-select d-inline-block" style="width: auto;" 
            onchange="window.location.href='{{ url_for('bill_drafting.workspace') }}?rep_id=' + this.value">
        {% for rep in all_reps %}
        <option value="{{ rep.id }}" {% if representative and rep.id == representative.id %}selected{% endif %}>
            {{ rep.name }} - District {{ rep.district }}
        </option>
        {% endfor %}
    </select>
</div>
{% endif %}
```

**Features:**
- Dropdown list of all representatives
- Shows representative name and district
- Changes workspace view when selection changes
- Preserves current selection

### 7. Result Template Updates
**File:** `templates/bill_drafting/result.html`

**Added Hidden Field for Admin:**
```html
{% if user.role == 'admin' and all_reps %}
<input type="hidden" name="rep_id" value="{{ request.args.get('rep_id', all_reps[0].id if all_reps else '') }}">
{% endif %}
```

**Purpose:** Ensures admin saves drafts to the correct representative when saving from AI-generated results

### 8. Generate Draft Route Updates
**File:** `routes/bill_drafting.py` - `generate_draft()` function

**Added:**
- Fetches all representatives if user is admin
- Passes `all_reps` to result template
- Passes `user` object to template for role checking

## Usage Guide for Admin Users

### Accessing Draft Workspace
1. Log in as admin
2. Navigate to "Draft Workspace" from sidebar
3. Use dropdown selector to choose which representative's workspace to view
4. View statistics, drafts, and comments for that representative

### Creating Drafts as Admin
1. Go to "AI Bill Drafting"
2. Fill in bill topic and description
3. Generate AI prompt
4. Save draft - it will be saved to currently selected representative

### Managing Existing Drafts
- **View:** Click any draft to see details
- **Edit:** Update visibility, title, or content
- **Delete:** Remove drafts if needed
- **Comment:** Add feedback on any draft

### Switching Between Representatives
Use the dropdown selector at the top of the workspace page to switch between different representatives' workspaces.

## Security Considerations

1. **Role Verification:** All routes verify user role before granting access
2. **Representative Validation:** Admin must select valid representative for actions
3. **Audit Trail:** All actions (create, update, delete) maintain proper user attribution
4. **Permission Checks:** Each route includes explicit admin role checks

## Testing Recommendations

To test admin access:

1. **Create Test Admin User:**
   ```python
   from models import User
   from extensions import db, bcrypt
   
   admin = User(
       username='testadmin',
       email='admin@test.com',
       password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
       role='admin'
   )
   db.session.add(admin)
   db.session.commit()
   ```

2. **Test Workflow:**
   - Login as admin
   - Access workspace and verify dropdown appears
   - Select different representatives from dropdown
   - Create a draft bill for a specific representative
   - Update visibility of existing drafts
   - Delete drafts
   - Verify all actions work correctly

3. **Verify Permissions:**
   - Ensure admin can access all representative features
   - Verify non-admin users cannot access features they shouldn't
   - Check that drafts are correctly attributed to representatives

## Future Enhancements

Potential improvements:

1. **Admin Dashboard:** Dedicated admin view showing all drafts across all representatives
2. **Bulk Actions:** Allow admin to perform actions on multiple drafts at once
3. **Activity Log:** Track which admin performed which actions on which drafts
4. **Representative Stats:** Show comparative statistics across representatives
5. **Draft Review Workflow:** Admin approval process for draft bills before going public

## Deployment Notes

- **Database:** No schema changes required
- **Migrations:** No database migrations needed
- **Dependencies:** No new dependencies added
- **Configuration:** No config changes required
- **Testing:** All existing tests remain valid

## Commit Information

- **Commit Hash:** e62ce5d
- **Files Changed:** 5 files
- **Lines Added:** 380
- **Lines Removed:** 19
- **Date:** November 7, 2025

## Related Documentation

- [Draft Workspace Feature](DRAFT_WORKSPACE_FEATURE.md)
- [Testing Quick Start](TESTING_QUICK_START.md)
- [README](README.md)
