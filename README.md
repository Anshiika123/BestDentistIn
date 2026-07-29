# BestDentistIn 🦷

**A local dental discovery and lead-generation platform — built for Roorkee, designed to scale to any city.**

Users search for dentists by city, locality, treatment, or problem, and connect with clinics directly via WhatsApp or phone call. Every click is tracked as a lead. No payments, no centralized booking engine, no AI diagnosis — just a fast, honest path from search to a clinic's front desk.

[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Table of contents

- [What this is](#what-this-is)
- [Feature overview](#feature-overview)
- [Tech stack](#tech-stack)
- [Project layout](#project-layout)
- [Getting started](#getting-started)
- [URL map](#url-map)
- [Data model](#data-model)
- [What's mocked vs. production-ready](#whats-mocked-vs-production-ready)
- [Roadmap](#roadmap)
- [Who uses what: admin vs. dashboard vs. portal](#who-uses-what-admin-vs-dashboard-vs-portal)
- [Deep dive: Phase 2 – SEO & lead-gen engine](#phase-2-seo--lead-generation-engine)
- [Deep dive: Phase 3 – clinic SaaS dashboard](#phase-3-clinic-saas-dashboard)
- [Deep dive: Phase 4 – AI-style patient intake](#phase-4-ai-patient-intake)
- [Design notes](#design-notes)

---

## What this is

BestDentistIn was built in four phases, each shipping a working, demoable slice:

| Phase | What it adds |
|---|---|
| **1 — Core discovery** | City/locality/treatment/problem pages, clinic profiles, WhatsApp & call lead capture |
| **2 — SEO & lead-gen engine** | JSON-LD/breadcrumb schema, page-view analytics (separate from leads), internal linking, sitemap/robots.txt, internal ops dashboard |
| **3 — Clinic SaaS dashboard** | `/portal/` — clinic logins, lead inbox with status/follow-up workflow, missed-lead tracking, notes, activity log, per-clinic analytics |
| **4 — AI-style patient intake** | `/intake/` — short questionnaire, rule-based problem classification, clinic routing (explicitly *not* a diagnosis) |

Roorkee is the only seeded city today, but the schema (`City` → `Locality`, city-scoped `Treatment`/`Problem`) is already built for multi-city expansion.

## Feature overview

- 🔍 **Discovery pages** for city, locality, treatment, and problem — each with real, non-duplicated content (unique FAQs, clinic lists, intro copy)
- 📲 **Lead capture** — every WhatsApp/call CTA routes through a tracking redirect before firing, so no click goes unlogged
- ✅ **Verification badge** — driven by a time-boxed `VerificationRecord`, not a static flag
- 📈 **SEO scaffolding** — canonical tags, breadcrumbs, JSON-LD (`Dentist`/`ItemList`/`Article`), sitemap, robots.txt
- 🧭 **Internal dashboard** (staff-only) — leads, page performance, and content breakdowns by city/treatment/problem
- 🏥 **Clinic portal** — a scoped, mobile-friendly SaaS dashboard for clinics to manage their own leads
- 🤖 **Patient intake** — rule-based symptom classification and clinic routing, with a clean seam to swap in a real LLM later
- 🧩 **Clean separation** — leads (conversions) and page views (traffic) are tracked in entirely separate tables, never conflated

## Tech stack

- **Backend**: Django 6 (Python 3.12)
- **Database**: SQLite for local dev, PostgreSQL-ready for production (env-switchable)
- **Frontend**: Django templates + Tailwind CSS (CDN in this build — see [mocked vs. production-ready](#whats-mocked-vs-production-ready))
- **Media**: Django's built-in static/media handling

## Project layout

```
bestdentistin/
  manage.py
  requirements.txt
  .env.example
  bestdentistin/          # project settings, root urls
  apps/
    core/                 # homepage, shared context processor, seed_roorkee/seed_portal_demo commands
    locations/             # City, Locality models + city/locality page views
    clinics/               # Clinic, Dentist, Treatment, Problem, Verification, FAQ, Review
    content/                # BlogCategory, BlogPost (+ Phase 2: category↔treatment/problem links)
    accounts/               # Phase 3: ClinicUser (links a Django User to a Clinic + role)
    leads/                  # Lead model + WhatsApp/Call click-tracking redirect views
                             #   + Phase 3: status/follow-up/assignment workflow, LeadNote, LeadActivityLog
    intake/                 # Phase 4: IntakeSession model, classifier.py, routing.py
    analytics/              # Phase 2: PageView model + track_pageview() — page opens, not leads
    seo/                    # Phase 2: schema.py, breadcrumbs.py, linking.py, sitemaps.py, robots.txt
    dashboard/              # Staff-only (BestDentistIn ops) leads/clinics/pages/content dashboard
    portal/                 # Phase 3: clinic-facing SaaS dashboard (/portal/) — separate from dashboard/
  templates/               # all HTML templates (base.html + per-app folders + partials/)
  static/                  # static assets (currently empty — Tailwind is CDN-loaded)
  media/                   # uploaded clinic/dentist/blog images
  fixtures/                # (reserved for exported fixtures if needed)
```

## Getting started

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt
cp .env.example .env                # defaults work out of the box for local dev (SQLite)

python manage.py migrate
python manage.py seed_roorkee       # generates realistic Roorkee seed data (~40 clinics)
python manage.py seed_portal_demo   # creates clinic portal logins + demo leads (Phase 3 testing)
python manage.py createsuperuser    # for /admin/ and /dashboard/ access

python manage.py runserver
```

Then visit:

| URL | What you'll see |
|---|---|
| `/` | Homepage |
| `/dentist-in-roorkee/` | City page |
| `/dentist-in-roorkee-civil-lines/` | Locality page |
| `/clinic/<slug>/` | Clinic profile |
| `/treatments/root-canal-treatment/` | Treatment page |
| `/problems/tooth-pain/` | Problem page |
| `/blog/` | Blog |
| `/intake/` | AI-style patient intake |
| `/portal/login/` | Clinic SaaS dashboard (needs `seed_portal_demo`) |
| `/admin/` | Django admin |
| `/dashboard/` | Internal ops dashboard (staff login required) |

`seed_roorkee` and `seed_portal_demo` are both idempotent — safe to re-run after pulling new code. Pass `--clinics 50` or `--seed 7` to `seed_roorkee` to vary the generated data. `seed_portal_demo` prints demo login credentials for a few clinics (owner + staff account each, password `clinic12345`).

## URL map

| Path | View | Notes |
|---|---|---|
| `/` | `core.views.home` | |
| `/dentist-in-<rest>/` | `locations.views.city_or_locality` | One route resolves both city (`rest == "roorkee"`) and locality (`rest == "roorkee-civil-lines"`) pages by matching against `<city.slug>-<locality.slug>` |
| `/clinic/<slug>/` | `clinics.views.clinic_detail` | |
| `/treatments/<slug>/` | `clinics.views.treatment_detail` | |
| `/problems/<slug>/` | `clinics.views.problem_detail` | |
| `/blog/`, `/blog/<slug>/` | `content.views.*` | |
| `/leads/go/whatsapp/<clinic_slug>/` | `leads.views.track_whatsapp` | Logs a `Lead`, then 302s to a prefilled `wa.me` link |
| `/leads/go/call/<clinic_slug>/` | `leads.views.track_call` | Logs a `Lead`, then 302s to `tel:<number>` |
| `/sitemap.xml` | `django.contrib.sitemaps.views.sitemap` | Sections registered in `apps/seo/sitemaps.py` |
| `/robots.txt` | `seo.views.robots_txt` | Disallows `/admin/`, `/dashboard/`, `/leads/go/` |
| `/dashboard/...` | `dashboard.views.*` | `@staff_member_required` |
| `/admin/` | Django admin | Primary content-management surface |

All CTA buttons route through `leads:track_whatsapp` / `leads:track_call` — never directly at `wa.me`/`tel:` — so every click is captured before the redirect fires.

## Data model

```
City ──< Locality ──< Clinic >── Treatment
                        │  \        │
                        │   >── Problem
                        ├──< Dentist
                        ├──< VerificationRecord
                        ├──< ClinicFAQ (also attachable to City/Locality/Treatment/Problem)
                        ├──< Review
                        └──< Lead >── Treatment / Problem (optional)

BlogCategory ──< BlogPost
```

- **City / Locality** — Roorkee is the only seeded `City`; `Locality.full_slug` generates the `dentist-in-roorkee-<locality>` slug used in routing.
- **Clinic** — owns FKs to City + Locality, M2M to Treatment/Problem, holds contact info (`phone_number`, `whatsapp_number`), exposes `is_verified` / `whatsapp_link` / `tel_link`.
- **VerificationRecord** — `Clinic.is_verified` looks at the most recent record and requires `is_verified`, `phone_confirmed`, `timings_confirmed`, and freshness within `VERIFICATION_FRESHNESS_DAYS` (default 180) — the "Verified" badge only shows when all four hold.
- **ClinicFAQ** — one flexible model with nullable FKs to Clinic/City/Locality/Treatment/Problem, serving every page type without duplicated models.
- **Lead** — one row per WhatsApp/Call click: clinic, city, locality, CTA type, page source, optional treatment/problem, referrer, user agent, IP.
- **Review** — placeholder model, seeded with mock reviews; not user-submittable yet.

## What's mocked vs. production-ready

**Production-ready:**
- Full relational schema and Django admin CRUD for every model
- Lead capture pipeline (click → DB row → redirect) with dashboard aggregation
- SEO scaffolding: meta title/description, canonical tags, breadcrumbs, JSON-LD schema, semantic H1/H2
- Verification-freshness logic driving the "Verified" badge
- City/locality/treatment/problem filtering on the city page

**Mocked / placeholder (documented, not hidden):**
- **Photos** (clinic, dentist, blog cover) — templates render an explicit placeholder when no image is uploaded; no fake stock photos shipped
- **Map embeds** — `Clinic.map_embed_url` exists; template currently shows a static placeholder box
- **Blog post bodies** — real titles/categories, short placeholder prose
- **Reviews** — seeded mock data, no public submission form yet
- **Tailwind via CDN** — fine for iteration speed, but ships the full JIT compiler to the browser; swap for a compiled build before production
- **"List Your Clinic" WhatsApp number** — placeholder (`919999999999`), replace with the real business number

## Roadmap

1. Compiled Tailwind build (drop the CDN script) + `django-compressor` or similar
2. Public clinic self-signup/claim flow (currently: WhatsApp the team → admin adds the clinic and creates the portal login)
3. Real Google Maps embed on clinic pages using `Clinic.map_embed_url`
4. Multi-city expansion — `City` and locality-aware routing already generalize; see the [Phase 2 notes](#phase-2-seo--lead-generation-engine) on city-scoped `Treatment`/`Problem`
5. WhatsApp Business API intake and an AI voice call bot — explicitly out of scope for now; see [Phase 4](#phase-4-ai-patient-intake) for the upgrade seam
6. Premium/featured listings — `Clinic.is_featured` already exists and is used on the homepage
7. Blog CMS — richer body field, real authored content
8. Public review submission form with moderation
9. Real analytics pipeline (GA4/Plausible) alongside the in-house `PageView` model
10. Real clinic notifications (email/SMS/WhatsApp) — see `apps/leads/notifications.py`, a documented no-op stub
11. Clinic staff invite flow — accounts are currently admin-created only

## Who uses what: admin vs. dashboard vs. portal

- **Django admin** (`/admin/`) — BestDentistIn's internal management backend: clinics (with inline dentists, verification records, FAQs, portal accounts), treatments, problems, blog posts, and read-only inspection of leads/page views/intake sessions. Staff/superusers only.
- **`/dashboard/`** — internal SEO/ops dashboard (staff-only), covering leads and content performance across all clinics.
- **`/portal/`** — the clinic's own dashboard, scoped to their clinic only. Clinics never see `/dashboard/` or `/admin/`.

---

## Phase 2: SEO & lead generation engine

Phase 2 doesn't add new page types — it makes the existing pages rank better and makes it possible to see, internally, which of them actually produce leads.

**New apps:**
- **`apps/analytics`** — `PageView`: one row per page open, with UTM params and referrer. A visitor browsing five pages produces five `PageView` rows and zero `Lead` rows unless they click WhatsApp or Call. `track_pageview()` seeds `request.session["utm"]` on first touch, so a later WhatsApp click still attributes back to the original campaign.
- **`apps/seo`** — no models, four helper modules used by every public view:
  - `schema.py` — JSON-LD builders (`BreadcrumbList`, `FAQPage`, `Dentist`/LocalBusiness, `Article`), combined via `to_json_ld()` into one `@graph` payload per page
  - `breadcrumbs.py` — one function per page type; the same source of truth powers both the visible breadcrumb nav and the schema
  - `linking.py` — the internal-linking engine (`nearby_localities`, `nearby_clinics`, related blog/treatment/problem links), city-agnostic
  - `sitemaps.py` — sitemap sections for cities, localities, treatments, problems, clinics, and blog posts

**Leads vs. page views — the important distinction:** only WhatsApp/Call clicks are leads; page opens are analytics. `Lead` gained `page_slug`, `cta_label`, and `utm_source`/`utm_medium`/`utm_campaign` so a lead traces back to the exact page and campaign that produced it.

**Dashboard additions:** total page views and CTR at `/dashboard/`, top lead-generating pages and low-conversion pages at `/dashboard/pages/`, city/treatment/problem breakdowns at `/dashboard/content/`.

**Multi-city status:** `Treatment` and `Problem` now carry a `city` FK (`unique_together = (city, slug)`), so a second city can have its own treatment/problem content without touching Roorkee's. URLs are still flat (`/treatments/<slug>/`) rather than city-prefixed — that change is deferred until a second city actually exists.

## Phase 3: Clinic SaaS Dashboard

A lightweight, mobile-friendly dashboard at `/portal/` so a clinic can manage its own leads without touching Django admin. Deliberately not a CRM: no pipelines, no email sequencing, no custom fields.

**Access model:** `apps.accounts.ClinicUser` links a Django `User` to one `Clinic` with a role (`owner`/`staff`). Accounts are created via Django admin only — no public signup. `clinic_login_required` scopes every query to the logged-in clinic; staff can only edit leads that are unassigned or assigned to them, while owners can edit and reassign anything.

**Lead workflow:** `Lead` gained `status`, `follow_up_type`, `follow_up_date`, `assigned_to`, `last_contacted_at`, `missed_reason`, and more. `LeadNote` holds free-text notes; `LeadActivityLog` is an append-only audit trail of every status/follow-up/assignment change. Missed-lead tracking is computed live at `/portal/reminders/` (any lead still `status=new` after 24 hours), not via a background job.

**Portal pages:** `/portal/login/`, `/portal/` (overview), `/portal/leads/` (filterable inbox), `/portal/leads/<id>/` (detail + notes + activity log), `/portal/analytics/`, `/portal/reminders/`, `/portal/settings/` (owner-only, and deliberately doesn't expose verification status, address, or treatments — those stay admin-managed).

## Phase 4: AI Patient Intake

A short, structured intake flow at `/intake/` that routes a patient to relevant clinics — **it never diagnoses**, and every page carries an explicit disclaimer.

**Why rule-based, not an LLM call:** `apps/intake/classifier.py` is a deterministic keyword matcher, deliberately. It never fabricates a diagnosis or a confidence it doesn't have, needs no API key or network call, and exposes a clean upgrade path — `classify(text)` returns a `ClassificationResult` dataclass (`problem`, `confidence`, `notes`, `matched_treatments`); swapping the body for a real LLM call changes nothing else in the app.

**Flow:** `/intake/` → single-page form (problem description, severity, duration, patient type, locality, preferred time, optional age/phone/language) → `IntakeSession` created and classified → `match_clinics()` ranks clinics (verified-first, matched treatment/problem, preferred locality, then city-wide fallback) → `/intake/<session_key>/` shows results with normal WhatsApp/Call CTAs. Clicking a CTA creates a real `Lead` linked back to the `IntakeSession` via the same tracking redirect every other page uses.

**Safety:** disclaimers appear on both the form and results page; `urgency` is the patient's own self-rating and only changes on-page messaging, never a clinical claim; classifier confidence/notes are admin-only, never shown to the patient.

**Not built here (by design):** WhatsApp bot intake, an AI voice call bot, multilingual routing, and a multi-turn chat UI — `IntakeSession.source_channel` and `language_preference` already exist as seams for these.

---

## Design notes

A separate project blueprint (different naming conventions — `LeadEvent`, `seo_title`, `/lead/whatsapp/`, etc.) was reviewed against this codebase. Rather than a full rename for no functional gain, two genuinely valuable pieces were adopted:

1. **City-scoped `Treatment`/`Problem`** — real multi-city support, wasn't in the original Phase 2 design
2. **`ClinicPhoto`** — a real gallery model wired into `clinic_detail.html`, replacing a permanent placeholder

**Deliberately not adopted:** the blueprint's `ClinicService` model — it would model exactly what `Clinic.treatments` already models, under a different name, with no independent purpose.
