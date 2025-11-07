#!/usr/bin/env python3
"""
Sync all Missouri House representatives to the database.
Primary source: Member Roster (by session/year):
  https://house.mo.gov/MemberRoster.aspx?year=2025&code=R
Fallback source: Member Grid (cluster view):
  https://house.mo.gov/MemberGridCluster.aspx
"""
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from main import app
from extensions import db
from models import Representative

ROSTER_URL = "https://house.mo.gov/MemberRoster.aspx?year=2025&code=R"
GRID_URL = "https://house.mo.gov/MemberGridCluster.aspx"

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RepSync/1.0)'}

def fetch_html(url: str) -> str | None:
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError) as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_from_roster(html: str) -> list[dict]:
    """Attempt to parse reps from the MemberRoster page.
    We look for tables with rows containing District/Party and a name split.
    Returns a list of dicts with keys: district, first_name, last_name, party, city, phone, room.
    """
    reps: list[dict] = []
    soup = BeautifulSoup(html, 'html.parser')

    # Generic approach: scan all rows, detect at least district/party columns.
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 5:
            continue
        texts = [td.get_text(strip=True) for td in tds]
        # Heuristic: District looks like digits, Party like R/D/I, Name split across First/Last or "Last, First"
        district = None
        party = None
        first_name = None
        last_name = None
        city = None
        phone = None
        room = None

        # Try patterns: look for a td with all digits as district
        for i, val in enumerate(texts):
            if val.isdigit():
                district = val
                # Look around for party and name
                # Party: short code like 'R' or 'D'
                # Name: might be 'Last' and 'First' as separate columns
                # We try both patterns.
                # Nearby cells within the row
                neighbors = texts[max(0, i-3): i+4]
                # Party
                for n in neighbors:
                    if n in ("R", "D", "I"):  # basic party codes
                        party = n
                        break
                # Name patterns
                # Case 1: separate Last, First in two columns (common on Grid)
                # We'll fallback to that in grid parser; roster may have "Last, First"
                for n in texts:
                    if "," in n and len(n.split(",")) == 2:
                        last_name = n.split(",")[0].strip()
                        first_name = n.split(",")[1].strip()
                        break
                break
        # Some rows might have city/phone/room further right
        if len(texts) >= 8:
            # Best-effort guess based on grid layout ordering
            city = texts[-3] if texts[-3] and len(texts[-3]) > 2 else city
            phone = texts[-2] if texts[-2] else phone
            room = texts[-1] if texts[-1] else room

        if district and (first_name or last_name):
            reps.append({
                'district': district,
                'first_name': first_name,
                'last_name': last_name,
                'party': party,
                'city': city,
                'phone': phone,
                'room': room,
            })

    return reps


def parse_from_grid(html: str) -> list[dict]:
    """Parse from MemberGridCluster.aspx known structure (8 columns)."""
    reps: list[dict] = []
    soup = BeautifulSoup(html, 'html.parser')
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) >= 8:
            try:
                last_name = tds[1].get_text(strip=True)
                first_name = tds[2].get_text(strip=True)
                district = tds[3].get_text(strip=True)
                party = tds[4].get_text(strip=True)
                city = tds[5].get_text(strip=True)
                phone = tds[6].get_text(strip=True)
                room = tds[7].get_text(strip=True)
                if last_name and first_name and district.isdigit() and last_name != 'Vacant':
                    reps.append({
                        'district': district,
                        'first_name': first_name,
                        'last_name': last_name,
                        'party': party,
                        'city': city,
                        'phone': phone,
                        'room': room,
                    })
            except Exception:
                continue
    return reps


def upsert_representatives(reps: list[dict]) -> tuple[int,int]:
    added = 0
    updated = 0
    for r in reps:
        dist = r.get('district')
        if not dist:
            continue
        rep = Representative.query.filter_by(district=dist).first()
        if not rep:
            rep = Representative(
                district=dist,
                first_name=r.get('first_name'),
                last_name=r.get('last_name'),
                party=r.get('party'),
                city=r.get('city'),
                phone=r.get('phone'),
                room=r.get('room'),
            )
            db.session.add(rep)
            added += 1
        else:
            rep.first_name = r.get('first_name') or rep.first_name
            rep.last_name = r.get('last_name') or rep.last_name
            rep.party = r.get('party') or rep.party
            rep.city = r.get('city') or rep.city
            rep.phone = r.get('phone') or rep.phone
            rep.room = r.get('room') or rep.room
            updated += 1
    db.session.commit()
    return added, updated


def main():
    print("Fetching representatives from roster page...")
    html = fetch_html(ROSTER_URL)
    reps = parse_from_roster(html) if html else []

    if not reps:
        print("Roster parse yielded 0 entries; falling back to grid page...")
        html2 = fetch_html(GRID_URL)
        reps = parse_from_grid(html2) if html2 else []

    if not reps:
        print("No representatives parsed. Exiting.")
        return

    with app.app_context():
        added, updated = upsert_representatives(reps)
        total = Representative.query.count()
        print(f"✓ Representatives sync complete: added={added}, updated={updated}, total={total}")


if __name__ == '__main__':
    main()
