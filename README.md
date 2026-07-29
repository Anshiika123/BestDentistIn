# BestDentistIn — Phase 1 + Phase 2 (Roorkee)

Local dental discovery and lead-generation site for **Roorkee only**. Users browse verified
dentists by city/locality/treatment/problem and contact clinics directly via WhatsApp or
phone call — every click is logged as a lead. No payments, no centralized booking engine,
no AI diagnosis.

**Phase 1** built the core discovery product (pages, clinic data, basic lead capture).
**Phase 2** turns it into an SEO + lead-generation engine: real JSON-LD/breadcrumb schema,
a page-view analytics layer separate from leads, an internal-linking engine, a sitemap/robots.txt,
and an internal dashboard for page/content performance. See [Phase 2: SEO & lead generation](#phase-2-seo--lead-generation-engine) below.

## Stack

- **Backend**: Django 6 (Python 3.12)
- **Database**: SQLite for local dev, PostgreSQL-ready for production (env-switchable)
- **Frontend**: Django templates + Tailwind CSS (via CDN in Phase 1 — see note below)
- **Media**: Django's built-in static/media handling

## Project layout

```
bestdentistin/
  manage.py
  requirements.txt
  .env.example
  bestdentistin/          # project settings, root urls
  apps/
    core/                 # homepage, shared context processor, seed_roorkee command
    locations/             # City, Locality models + city/locality page views
    clinics/               # Clinic, Dentist, Treatment, Problem, Verification, FAQ, Review
    content/                # BlogCategory, BlogPost (+ Phase 2: category↔treatment/problem links)
    leads/                  # Lead model + WhatsApp/Call click-tracking redirect views (CTA-only)
    analytics/              # Phase 2: PageView model + track_pageview() — page opens, not leads
    seo/                    # Phase 2: schema.py, breadcrumbs.py, linking.py, sitemaps.py, robots.txt
    dashboard/              # Staff-only leads/clinics/pages/content-performance dashboard
  templates/               # all HTML templates (base.html + per-app folders + partials/)
  static/                  # static assets (currently empty — Tailwind is CDN-loaded)
  media/                   # uploaded clinic/dentist/blog images
  fixtures/                # (reserved for exported fixtures if needed)
```

## Setup & run instructions

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt
cp .env.example .env                # defaults work out of the box for local dev (SQLite)

python manage.py migrate
python manage.py seed_roorkee       # generates realistic Roorkee seed data (~40 clinics)
python manage.py createsuperuser    # for /admin/ and /dashboard/ access

python manage.py runserver
```

Visit:
- `http://127.0.0.1:8000/` — homepage
- `http://127.0.0.1:8000/dentist-in-roorkee/` — city page
- `http://127.0.0.1:8000/dentist-in-roorkee-civil-lines/` — locality page
- `http://127.0.0.1:8000/clinic/<slug>/` — clinic profile
- `http://127.0.0.1:8000/treatments/root-canal-treatment/` — treatment page
- `http://127.0.0.1:8000/problems/tooth-pain/` — problem page
- `http://127.0.0.1:8000/blog/` — blog
- `http://127.0.0.1:8000/admin/` — Django admin (content management)
- `http://127.0.0.1:8000/dashboard/` — internal leads dashboard (staff login required)

Re-running `seed_roorkee` is idempotent (`update_or_create` on slugs) — safe to run again
after pulling new code. Pass `--clinics 50` or `--seed 7` to vary the generated data.

## URL / routing design

| Path | View | Notes |
|---|---|---|
| `/` | `core.views.home` | |
| `/dentist-in-<rest>/` | `locations.views.city_or_locality` | Single route resolves both the city page (`rest == "roorkee"`) and locality pages (`rest == "roorkee-civil-lines"`) by matching `rest` against `<city.slug>-<locality.slug>`. Avoids duplicating near-identical view logic across two URL patterns while keeping the exact `/dentist-in-roorkee-civil-lines/` URL shape from the spec. |
| `/clinic/<slug>/` | `clinics.views.clinic_detail` | |
| `/treatments/<slug>/` | `clinics.views.treatment_detail` | |
| `/problems/<slug>/` | `clinics.views.problem_detail` | |
| `/blog/`, `/blog/<slug>/` | `content.views.*` | |
| `/leads/go/whatsapp/<clinic_slug>/` | `leads.views.track_whatsapp` | Logs a `Lead`, then 302s to a `wa.me` link with a dynamically prefilled message. |
| `/leads/go/call/<clinic_slug>/` | `leads.views.track_call` | Logs a `Lead`, then 302s to `tel:<number>`. |
| `/sitemap.xml` | `django.contrib.sitemaps.views.sitemap` | Sections registered in `apps/seo/sitemaps.py`. |
| `/robots.txt` | `seo.views.robots_txt` | Disallows `/admin/`, `/dashboard/`, `/leads/go/`; points at the sitemap. |
| `/dashboard/`, `/dashboard/leads/`, `/dashboard/pages/`, `/dashboard/content/`, `/dashboard/clinics/` | `dashboard.views.*` | `@staff_member_required` |
| `/admin/` | Django admin | Primary content-management surface |

All CTA buttons in templates point at the `leads:track_whatsapp` / `leads:track_call` routes
(not directly at `wa.me`/`tel:`) so every click is captured before the redirect fires.

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

- **City / Locality** (`apps/locations`): Roorkee is the only seeded `City`; `Locality.full_slug`
  generates the combined `dentist-in-roorkee-<locality>` slug used in routing.
- **Clinic** (`apps/clinics`): owns FKs to City + Locality, M2M to Treatment/Problem,
  holds contact info (`phone_number` for display, `whatsapp_number` in `wa.me`-ready
  international format), and exposes `is_verified` / `whatsapp_link` / `tel_link` as
  computed properties.
- **VerificationRecord**: a clinic can have multiple records over time; `Clinic.is_verified`
  looks at the most recent one and requires `is_verified=True`, `phone_confirmed=True`,
  `timings_confirmed=True`, and `last_verified_at` within `VERIFICATION_FRESHNESS_DAYS`
  (default 180, configurable via `.env`) — the "Verified" badge only shows when all four hold.
- **ClinicFAQ**: a single flexible model with nullable FKs to Clinic/City/Locality/Treatment/
  Problem so the same FAQ system serves every page type without four near-duplicate models.
- **Lead** (`apps/leads`): one row per WhatsApp/Call click, capturing clinic, city, locality,
  CTA type, page source, optional treatment/problem context, referrer, user agent, and IP.
- **Review**: placeholder model, seeded with mock reviews; not user-submittable in Phase 1
  (no public review form is exposed).

## What's mocked vs. production-ready

**Production-ready:**
- Full relational schema and Django admin CRUD for every model
- Lead capture pipeline (click → DB row → redirect) with dashboard aggregation
- SEO scaffolding: per-page meta title/description, canonical tags, breadcrumbs,
  JSON-LD (`Dentist`/`ItemList`/`Article` schema), semantic H1/H2 structure
- Verification-freshness logic driving the "Verified" badge
- City/locality/treatment/problem filtering on the city page

**Mocked / placeholder (documented, not hidden):**
- **Clinic photos, dentist photos, blog cover images**: templates render an explicit
  "placeholder" block when no image is uploaded — no fake stock photos are shipped.
- **Map embeds**: `Clinic.map_embed_url` exists but the clinic template shows a static
  "Map embed placeholder" box — wire up a real Google Maps embed in Phase 2.
- **Blog post bodies**: seeded with short placeholder paragraphs under real, on-topic
  titles/categories — structure (slugs, categories, schema) is real, prose is not.
- **Reviews**: seeded mock reviews; there's no public submission form.
- **Tailwind via CDN** (`<script src="https://cdn.tailwindcss.com">` in `base.html`): fine for
  Phase 1 iteration speed, but ships the full JIT compiler to the browser. Swap for a
  compiled Tailwind build (`npm install -D tailwindcss` + a build step feeding
  `static/css/tailwind.css`) before production.
- **"List Your Clinic" WhatsApp number** in the header/homepage CTA is a placeholder
  (`919999999999`) — replace with the real BestDentistIn business number.

## SEO notes

- Every public template extends `base.html`, which renders `{% block meta_title %}` /
  `{% block meta_description %}` / a canonical `<link>` from `request.path`, and a
  `{% block schema %}` for page-specific JSON-LD.
- Clinic, treatment, and problem pages carry real (non-doorway) unique content — no two
  locality pages are copy-pasted; each pulls its own FAQ, clinic list, and (optionally)
  custom `intro_content` from the admin.
- `sitemap.xml` and `robots.txt` are live — see [Phase 2](#phase-2-seo--lead-generation-engine).

## Next steps (post–Phase 2)

1. Compiled Tailwind build (drop the CDN script) + `django-compressor` or similar.
2. Public clinic self-signup/claim flow (currently: WhatsApp the team, they get added via admin).
3. Real Google Maps embed on clinic pages using `Clinic.map_embed_url`.
4. Multi-city expansion: `City` and locality-aware routing already generalize; `Treatment`/
   `Problem` are currently global (not city-scoped) — see the Phase 2 section for what that
   means for queries like "braces cost in Dehradun" and the extension path.
5. WhatsApp Business API bot intake, AI call-bot intake, and appointment routing are
   explicitly **out of scope** — the `Lead` model's `page_source`/`cta_type`/UTM fields are
   structured so a future automation layer can consume them without a schema change.
6. Premium/featured listings: `Clinic.is_featured` already exists and is used on the
   homepage — a payments/ranking layer can build on top of it later.
7. Blog CMS: current `BlogPost` model is basic `TextField` body; consider a rich-text or
   Markdown field, plus real authored content to replace the seeded placeholders.
8. Public review submission form with moderation (the `Review` model exists; there's no
   public write path yet).
9. A real analytics pipeline (GA4/Plausible) alongside `PageView` — the in-house model is
   deliberately minimal (page-level counts for the internal dashboard), not a GA replacement.

## Admin / dashboard

- **Django admin** (`/admin/`) is the primary content-management interface: add/edit
  clinics (with inline dentists, verification records, and FAQs), treatments, problems,
  blog posts (including category↔treatment/problem links), and view leads/page views (read-only).
- **`/dashboard/`** is a lightweight, staff-only custom view layer on top of the same data —
  see [Phase 2 dashboard pages](#dashboard-additions) below. It intentionally does not
  duplicate admin's CRUD forms.

---

## Phase 2: SEO & lead generation engine

Phase 2 doesn't add new page *types* — it makes the existing city/locality/treatment/problem/
clinic/blog pages rank better and makes it possible to see, internally, which of them actually
produce leads.

### New apps

- **`apps/analytics`** — `PageView`: one row per page open (city/locality/clinic/treatment/
  problem/blog/home), with UTM params and referrer. This is analytics, not leads — a visitor
  browsing five pages produces five `PageView` rows and zero `Lead` rows unless they click
  WhatsApp or Call. `track_pageview()` also seeds `request.session["utm"]` on first touch, so
  a WhatsApp click several pages into the visit still attributes back to the campaign that
  brought the visitor in (see `apps/leads/views.py::_resolve_utm`).
- **`apps/seo`** — no models; four helper modules used by every public view:
  - `schema.py` — builds JSON-LD dicts (`BreadcrumbList`, `FAQPage`, `Dentist`/LocalBusiness,
    `Article`, `ItemList`) and `to_json_ld(*schemas)` combines them into one `@graph` payload
    per page, rendered by `base.html`'s `{% block schema %}`.
  - `breadcrumbs.py` — one function per page type, returning the same `(label, url)` list
    consumed by both the visible breadcrumb nav (`partials/breadcrumbs.html`) and
    `schema.breadcrumb_list_schema()` — one source of truth, no drift between what users see
    and what search engines see.
  - `linking.py` — the internal-linking engine: `nearby_localities`, `nearby_clinics`,
    `related_blog_posts_for_treatment`/`_problem`, `related_pages_for_blog_post`. City-agnostic
    (works off `clinic.city`/`locality.city`, never a hardcoded slug).
  - `sitemaps.py` — `Sitemap` subclasses for cities, localities, treatments, problems, clinics,
    and blog posts, registered at `/sitemap.xml`. `/robots.txt` (in `seo/views.py`) disallows
    `/admin/`, `/dashboard/`, and `/leads/go/` (the tracking redirects shouldn't be crawled).

### Leads vs. page views — the important distinction

> Only WhatsApp/Call clicks are leads. Page opens are analytics.

- `apps.leads.Lead` — created **only** by `/leads/go/whatsapp/...` and `/leads/go/call/...`.
  Phase 2 added `page_slug`, `cta_label`, and `utm_source`/`utm_medium`/`utm_campaign` so a
  lead can be traced back to the exact page and campaign that produced it, not just the page
  *type*.
- `apps.analytics.PageView` — created by every public detail/list view via `track_pageview()`
  (called once per request, right where the view already has the relevant objects in scope —
  see `apps/locations/views.py`, `apps/clinics/views.py`, `apps/content/views.py`,
  `apps/core/views.py`). Never touches the `Lead` table.
- The blog got a light restructure to make "blog CTA click" a real, traceable lead rather than
  a vague concept: `blog_detail` now pulls a few clinics that offer the post's most relevant
  related treatment and renders them with normal WhatsApp/Call CTAs (`page_source=blog`) —
  see `apps/content/views.py::blog_detail`.

### Content model enhancements

- `BlogCategory` gained `treatments`/`problems` M2M fields (to `clinics.Treatment`/`Problem`).
  This is what powers "related blog posts" on treatment/problem pages and "related treatment/
  problem pages" on blog posts — curated via the admin, not string-matching. `seed_roorkee`
  populates realistic links (e.g. category "Root Canal" → treatment `root-canal-treatment` +
  problems `tooth-pain`, `cavity`).
- `Lead` gained `page_slug`, `cta_label`, `utm_source`, `utm_medium`, `utm_campaign`.

### Dashboard additions

- `/dashboard/` (overview) — added total page views and overall CTR (leads ÷ views) alongside
  the Phase 1 lead counts.
- `/dashboard/pages/` — **top lead-generating pages** (grouped by page type + slug) and
  **pages with traffic but weak conversion** (≥3 views, sorted by lowest CTR) — the list a
  growth operator checks first: what's working, and what's getting search traffic but failing
  to convert.
- `/dashboard/content/` — views/leads/CTR broken down by city, by treatment, and by problem.
- `/dashboard/leads/` (Phase 1, extended) — now shows `page_slug` and `utm_source` per lead.

### Search-intent → page-type mapping (Phase 2 design, not new code)

The routing already in place satisfies the brief's intent map without new machinery:

| Query pattern | Page type | Route |
|---|---|---|
| "dentist near me" / "dentist in Roorkee" | City page | `/dentist-in-<city>/` |
| "dentist in Civil Lines Roorkee" | Locality page | `/dentist-in-<city>-<locality>/` |
| "root canal in Roorkee" | Treatment page | `/treatments/<slug>/` |
| "tooth pain dentist Roorkee" / "best dentist for tooth pain" | Problem page (+ clinic list) | `/problems/<slug>/` |
| "braces cost in Dehradun" (future city) | Treatment page, city-scoped | See note below |

**Multi-city caveat**: `Treatment`/`Problem` are currently global rows (shared across all
cities), so `/treatments/braces-orthodontics/` can't yet show a *different* fee range or copy
for Dehradun vs. Roorkee — today it's one page per treatment, city-agnostic content, with a
city-scoped clinic list underneath it. Making "braces cost in Dehradun" its own indexable page
means either (a) a `TreatmentCityPage` model (treatment × city → override fee range/copy/meta)
or (b) city-prefixed treatment slugs (`/treatments/braces-dehradun/`). Neither is built in
Phase 2 — deliberately, per the "don't build for cities that don't exist yet" constraint — but
`nearby_clinics`/`related_blog_posts_for_treatment`/breadcrumbs already take a `city` argument,
so adding (a) later doesn't require touching the linking or schema layers.

### What's still mocked in Phase 2

- No real analytics warehouse — `PageView` is a lightweight in-app table for the internal
  dashboard, not a GA4/Plausible replacement (see Next Steps).
- UTM attribution is session-based (first-touch within a browser session), not a persistent
  cross-session identity — fine for a single-session "ad click → WhatsApp lead" flow, not for
  multi-session attribution.
- `robots.txt`/`sitemap.xml` are functionally complete but untested against a real search
  console — verify indexing status after the first production deploy.
