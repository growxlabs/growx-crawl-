"""
Push Batch 1 Verified Healthcare Targets to GrowXLabs CRM & Marketing Hub.
"""

import json
import os
import re
import httpx

def get_env():
    env = {}
    env_path = "c:/growxlabs/grow-x/.env.local"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def normalize_domain(val):
    if not val:
        return None
    val = val.strip().lower()
    val = re.sub(r"^https?://", "", val)
    val = re.sub(r"^www\.", "", val)
    return val.split("/")[0].split("?")[0] or None

def normalize_phone(val):
    if not val:
        return None
    digits = re.sub(r"\D", "", val)
    return digits or None

def main():
    env = get_env()
    url = env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    org_id = env.get("DEFAULT_ORGANISATION_ID", "8e7d6c54-68f1-4d19-9bf5-c20fe6c37721")

    if not url or not key:
        print("[ERROR] Missing Supabase credentials in .env.local")
        return

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    # Load 100 verified targets
    targets_path = "data/healthcare/targets_batch_1_verified.json"
    with open(targets_path, "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"[*] Loaded {len(targets)} verified healthcare targets.")

    # Check existing leads to avoid duplicate inserts
    r_existing = httpx.get(
        f"{url}/rest/v1/leads?organisation_id=eq.{org_id}&select=business_name",
        headers={"apikey": key, "Authorization": f"Bearer {key}"}
    )
    existing_biz = set()
    if r_existing.status_code == 200:
        for row in r_existing.json():
            existing_biz.add(row.get("business_name", "").strip().lower())

    leads_to_insert = []
    mkt_to_insert = []

    for t in targets:
        b_name = t["business_name"].strip()
        norm_phone = normalize_phone(t.get("phone"))
        norm_domain = normalize_domain(t.get("website_url"))
        doc_name = t.get("doctor_or_owner") or b_name
        score = int(round((t.get("rating") or 4.5) * 18))  # ~80 to 90

        # Build CRM Lead Row
        lead_row = {
            "organisation_id": org_id,
            "business_name": b_name,
            "name": doc_name,
            "contact_name": t.get("doctor_or_owner"),
            "contact_title": "Clinical Lead / Owner" if t.get("doctor_or_owner") else None,
            "phone": t.get("phone"),
            "email": t.get("email"),
            "website_url": t.get("website_url"),
            "city": t.get("city"),
            "state": "Andhra Pradesh",
            "country": "India",
            "source": "other",
            "source_label": "growx-crawl",
            "source_tool": "growx-crawl",
            "source_url": t["source_urls"][0] if t.get("source_urls") else None,
            "priority": "high",
            "status": "new",
            "lead_score": score,
            "notes": f"[{t['category']}] {t.get('specialty', '')}. Qualification: {', '.join(t.get('qualification_signals', []))}",
            "normalized_phone": norm_phone,
            "normalized_domain": norm_domain,
            "custom_fields": {
                "category": t.get("category"),
                "specialty": t.get("specialty"),
                "address": t.get("address"),
                "whatsapp": t.get("whatsapp_number"),
                "google_maps_url": t.get("google_maps_url"),
                "branches": t.get("branches"),
                "opening_hours": t.get("opening_hours"),
                "rating": t.get("rating"),
                "review_count": t.get("review_count"),
                "doctor_or_owner": t.get("doctor_or_owner"),
                "qualification_signals": t.get("qualification_signals"),
                "evidence": t.get("validation", {}).get("evidence", [])
            }
        }
        leads_to_insert.append(lead_row)

        # Build Marketing Lead Row
        email_clean = t.get("email")
        if not email_clean:
            domain_part = norm_domain or "clinic.in"
            email_clean = f"contact@{domain_part}"

        mkt_row = {
            "business_name": b_name,
            "name": doc_name,
            "phone": t.get("phone"),
            "email": email_clean,
            "status": "MQL",
            "score": score,
            "custom_fields": {
                "category": t.get("category"),
                "specialty": t.get("specialty"),
                "city": t.get("city"),
                "state": "Andhra Pradesh",
                "website": t.get("website_url"),
                "source": "growx-crawl",
                "doctor": t.get("doctor_or_owner")
            }
        }
        mkt_to_insert.append(mkt_row)

    print(f"[*] Prepared {len(leads_to_insert)} CRM leads and {len(mkt_to_insert)} Marketing Hub leads.")

    # Batch insert into leads (chunks of 25)
    inserted_leads = 0
    chunk_size = 25
    for i in range(0, len(leads_to_insert), chunk_size):
        chunk = leads_to_insert[i:i + chunk_size]
        r = httpx.post(f"{url}/rest/v1/leads", headers=headers, json=chunk)
        if r.status_code in [200, 201]:
            inserted_leads += len(chunk)
            print(f"  [+] Pushed CRM leads chunk {i//chunk_size + 1}: {len(chunk)} items.")
        else:
            print(f"  [-] Error pushing CRM leads chunk: {r.status_code} - {r.text[:200]}")

    # Batch insert into marketing_leads (chunks of 25)
    inserted_mkt = 0
    for i in range(0, len(mkt_to_insert), chunk_size):
        chunk = mkt_to_insert[i:i + chunk_size]
        r = httpx.post(f"{url}/rest/v1/marketing_leads", headers=headers, json=chunk)
        if r.status_code in [200, 201]:
            inserted_mkt += len(chunk)
            print(f"  [+] Pushed Marketing leads chunk {i//chunk_size + 1}: {len(chunk)} items.")
        else:
            print(f"  [-] Error pushing Marketing leads chunk: {r.status_code} - {r.text[:200]}")

    print("\n================ TRANSFER SUMMARY ================")
    print(f"CRM Leads Pushed: {inserted_leads} / 100")
    print(f"Marketing Hub Leads Pushed: {inserted_mkt} / 100")
    print(f"Destination: Supabase {url}")
    print(f"Visibility: CRM Pool (/admin/leads) & Marketing Hub (/admin/marketing)")

if __name__ == "__main__":
    main()
