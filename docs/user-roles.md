# User Roles & Permissions

Purp supports multiple user roles with different levels of access and capabilities.

## Role Hierarchy

1. **Regular User** (Default)
2. **Power User**
3. **Candidate**
4. **Rep Staffer**
5. **Representative**
6. **Admin**

## Role Descriptions

### Regular User

Default role for all new registrations.

**Permissions:**
- View bills and representatives
- Comment on legislation
- Support/oppose bills
- Message representatives
- RSVP to events
- Purchase event tickets
- Support users running for office
- Manage personal profile

### Power User

Enhanced permissions for active community members.

**Additional Permissions:**
- Enhanced comment capabilities
- Priority messaging (configurable)
- Early event access (configurable)

### Candidate

Users who have indicated they are thinking about running for office.

**Additional Permissions:**
- Create and manage events
- Send event invitations
- Marked with ~* symbol in comments
- Profile displays supporter count
- Event creation capabilities

**How to Become a Candidate:**
1. Edit your profile
2. Check "Thinking about running for office"
3. Save changes

### Rep Staffer

Staff members working for a representative.

**Additional Permissions:**
- Manage events for their representative
- Send event invitations on behalf of representative
- View constituent messages
- RSVP management

### Representative

Elected officials with a Representative profile in the system.

**Additional Permissions:**
- Full event management
- Create event templates
- Send invitations to constituents
- View all constituent messages
- Manage event purchases
- Access to constituent engagement metrics

**How to Become a Rep:**
- Admin must link your user account to a Representative profile

### Admin

Full system access for platform administrators.

**Permissions:**
- All permissions from other roles
- Create events for any representative
- Manage all users
- Access system configuration
- Database management
- View all messages and activities

## Permission Matrix

| Feature | Regular | Power | Candidate | Staffer | Rep | Admin |
|---------|---------|-------|-----------|---------|-----|-------|
| View Bills | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Comment | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Support/Oppose Bills | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Message Reps | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RSVP Events | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Purchase Tickets | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Support Candidates | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create Events | - | - | ✓ | ✓* | ✓ | ✓ |
| Manage Own Events | - | - | ✓ | ✓* | ✓ | ✓ |
| Send Invitations | - | - | ✓ | ✓* | ✓ | ✓ |
| View Messages | - | - | - | ✓* | ✓ | ✓ |
| Create Templates | - | - | - | - | ✓ | ✓ |
| Manage All Events | - | - | - | - | - | ✓ |
| Manage Users | - | - | - | - | - | ✓ |
| System Config | - | - | - | - | - | ✓ |

\* Only for their assigned representative

## Role Assignment

### For Users
- **Regular → Power**: Admin assignment (manual)
- **Regular → Candidate**: Self-service via profile settings
- **Any → Staffer**: Admin assignment with representative link
- **Any → Representative**: Admin assignment with representative profile link
- **Any → Admin**: Admin assignment (manual)

### For Admins

Admins can change user roles through the admin interface or database directly:

```python
from models import User
from extensions import db

user = User.query.filter_by(username='johndoe').first()
user.role = 'power'  # or 'candidate', 'rep_staffer', 'rep', 'admin'
db.session.commit()
```

## Special Indicators

### Candidate Symbol (~*)
Users marked as "thinking about running for office" display a special ~* symbol next to their username in:
- Comments on bills
- Profile pages
- Supporter lists

### Support Counts
Candidates can see how many users support them running for office. This count is displayed:
- On their profile
- In comment sections
- On representative detail pages (if they're linked to a rep)

## Security Considerations

- Role changes are logged for audit purposes
- Permissions are checked server-side on every request
- Admin actions require additional authentication
- Sensitive operations use CSRF protection
- Role escalation attempts are blocked and logged
