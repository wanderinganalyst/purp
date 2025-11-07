# Event Templates System - Quick Reference

## Overview
The event templates system allows representative users to create events with purchasable options like seats, merchandise, food, and transportation.

## Pre-configured Templates

### 1. Rally Template
Political rally with the following purchasable options:

**Seating (3 options):**
- Front Row Seat - $50.00
- Standard Seat - $25.00
- VIP Section - $100.00

**Merchandise (5 options):**
- Campaign Flag - $15.00
- Rally Hat - $20.00
- Rally Towel - $10.00
- Campaign Pin - $5.00
- Campaign Sticker - $2.00

**Transportation (1 option):**
- Bus Transportation - $10.00

### 2. Dinner Event Template
Fundraising dinner with the following purchasable options:

**Seating (3 options):**
- Head Table Seat - $200.00
- Full Table (8 seats) - $1,000.00
- Single Seat - $150.00

**Food & Drinks (4 options):**
- Catered Meal - $75.00
- Vegetarian Meal - $75.00
- Wine Pairing - $30.00
- Premium Bar Package - $50.00

**Merchandise (5 options):**
- Event Flag - $15.00
- Event Hat - $20.00
- Event Towel - $10.00
- Commemorative Pin - $5.00
- Event Sticker - $2.00

**Transportation (2 options):**
- Valet Parking - $25.00
- Shuttle Service - $15.00

## How to Use (For Rep Users)

### Creating an Event with a Template:
1. Log in as a rep user
2. Navigate to "Manage Events" in the sidebar
3. Click "Create Event"
4. Fill in event details (title, date, location)
5. Select "Rally Template" or "Dinner Event Template" from the dropdown
6. Submit the form

### Creating Custom Templates:
1. Navigate to "Event Templates" in the sidebar
2. Click "Create Template"
3. Enter template name and description
4. After creation, add purchasable options:
   - Option name (e.g., "Front Row Seat")
   - Option type (seating, food, merchandise, transportation, other)
   - Price
   - Optional description

### Managing Template Options:
- Edit template options from the "Event Templates" page
- Add new options at any time
- Delete options (will not affect past purchases)
- Options can be toggled active/inactive

## Public Event Pages
When a constituent views an event with a template:
- They see all active purchasable options grouped by type
- They can select quantities for each option
- Purchase form shows total price
- All purchases are tracked in the database

## Database Structure

**Tables:**
- `event_templates` - Template definitions
- `event_options` - Purchasable options for each template
- `event_purchases` - User purchases for events
- `events` - Events with optional template_id link

**Relationships:**
- Event → EventTemplate (many-to-one)
- EventTemplate → EventOptions (one-to-many)
- Event → EventPurchases (one-to-many)
- User → EventPurchases (one-to-many)

## Routes

**Rep-only routes:**
- `/rep/events` - Manage events
- `/rep/events/create` - Create event (with template selection)
- `/rep/events/<id>/edit` - Edit event
- `/rep/events/<id>/delete` - Delete event
- `/rep/templates` - Manage templates
- `/rep/templates/create` - Create template
- `/rep/templates/<id>/options` - Edit template options
- `/rep/templates/<id>/options/<option_id>/delete` - Delete option

**Public routes:**
- `/event/<id>` - View event and purchase options
- `/event/<id>/purchase` - Process purchase (login required)

## Extending the System

To add more templates, either:
1. Use the web UI (rep users only)
2. Create a seed script similar to `seed_templates.py`
3. Directly insert into database via Python shell

To add new option types:
- Update the option_type dropdown in templates
- No code changes needed - system supports any option type
