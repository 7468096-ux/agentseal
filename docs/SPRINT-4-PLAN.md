# Sprint 4: Make It Live

## Goal: Close all critical gaps so the product feels real

### Step 1: Directory Search + Filters (HIGH)
- Add search bar to /directory (search by name/slug/description)
- Add filters: platform, trust tier, category
- Add sorting: by trust score, by name, by date
- Update /v1/agents endpoint to support query params

### Step 2: Profile → Action Link (CRITICAL)
- Add "Visit Agent" button on profile (links to website_url)
- Add "Contact Owner" section (show owner_email if verified)
- For unclaimed: show "Claim this agent" prominently
- For claimed without website: show "No website provided"

### Step 3: User Accounts + Report UI (MEDIUM)
- Simple email-based user registration (POST /v1/users)
- User login via API key (same pattern as agents)
- "Rate this agent" button on profile page
- Simple form: outcome (success/failure), comment, task type
- UI renders the form, submits to /v1/agents/{id}/reports

### Step 4: Certification Improvements (MEDIUM)
- Expand task pool: 30 tasks per difficulty (90 total)
- Randomize input data per attempt (not just task selection)
- Add cooldown enforcement (24h between attempts)
- Add attempt count enforcement (3/month)

### Step 5: Seed Real Data (MEDIUM)
- Claim Alice (our agent) — full profile with avatar, description
- Generate 20+ behaviour reports for Alice (from our real usage)
- Have Alice take Bronze certification
- This makes at least 1 agent look "alive"

### Step 6: Polish (LOW)
- Fix unclaimed profiles to hide empty stats
- Add "No activity yet" for agents with 0 reports
- Email field in claim form
- Better error pages (404, 500)
