# Sendit — Trusted Moving, Planning & Inventory Platform

Sendit helps people:
- find a **trustworthy, verified moving company**,
- **plan and manage their time** leading up to moving day, and
- **catalog their belongings** with a detailed inventory checklist,

through a simple 4-step flow: **Enter Details → Get Your Price → Book Your Move → Track & Communicate**.

This is a full rebuild of the original prototype. See "What was fixed" below for the list of bugs and
missing features from the original codebase that this version resolves.

---

## 1. Tech stack

- **Python 3.11+**, **Django 5.2 (LTS)**
- SQLite for local development, optional PostgreSQL in production via `DATABASE_URL`
- **Bootstrap 5** (vendored locally, no CDN dependency) + a custom design system in `static/css/styles.css`
- `django-bootstrap-icons` for inline SVG icons
- **WhiteNoise** for serving static files in production without a separate CDN/server
- **Safaricom Daraja (M-Pesa) STK Push** for payments
- `python-dotenv` for local secret management via a `.env` file

---

## 2. Project structure

```
sendit/
├── manage.py
├── requirements.txt
├── .env.example          # copy to .env and fill in secrets
├── Sender/                # project config (settings, urls, wsgi/asgi)
├── app/                   # the Sendit application
│   ├── models.py          # Profile, MovingCompany, Booking, MoveTask,
│   │                       # InventoryItem, Message, Payment
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   ├── mpesa.py            # M-Pesa Daraja helper (lazy, no import-time calls)
│   ├── pricing.py           # instant quote calculation
│   ├── management/commands/seed_demo_data.py
│   └── migrations/
├── templates/              # all HTML templates, one shared base.html
└── static/
    ├── css/styles.css      # new unified design system
    ├── css/bootstrap.min.css
    ├── js/bootstrap.bundle.min.js
    └── images/             # your original images, untouched
```

---

## 3. Running it locally in VS Code (step by step)

### 3.1 Prerequisites
- Python 3.11 or newer installed (`python3 --version`)
- VS Code with the **Python extension** (Microsoft) installed
- Git (optional, for version control)

### 3.2 Open the project
1. Unzip the project folder.
2. In VS Code: **File → Open Folder…** → select the `sendit` folder.

### 3.3 Create and activate a virtual environment
Open a terminal in VS Code (`` Ctrl+` ``):

```bash
python3 -m venv venv
```

Activate it:
- **macOS/Linux:** `source venv/bin/activate`
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **Windows (cmd):** `venv\Scripts\activate.bat`

VS Code will usually prompt "Select a Python Interpreter" — choose the one inside `venv`
(bottom-right corner of the window also lets you pick it).

### 3.4 Install dependencies
```bash
pip install -r requirements.txt
```

### 3.5 Set up your environment variables
```bash
cp .env.example .env
```
Open `.env` and at minimum set a real `SECRET_KEY` for anything beyond quick local testing. You can
generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
You can leave the `MPESA_*` values blank for now — the app runs fine without them; only the "Pay Now"
feature needs them (see section 6).

### 3.6 Run migrations
```bash
python manage.py migrate
```

### 3.7 Create an admin (superuser) account
```bash
python manage.py createsuperuser
```

### 3.8 (Optional but recommended) Seed demo data
This creates 3 sample moving companies and one demo user for each role so you can test every flow
immediately:
```bash
python manage.py seed_demo_data
```
This creates:
| Username | Password | Role |
|---|---|---|
| `demo_client` | `Demo1234!` | Client |
| `demo_driver` | `Demo1234!` | Driver |
| `demo_admin` | `Demo1234!` | Admin (also staff, can access `/admin/`) |

### 3.9 Run the development server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser. Django admin is at **http://127.0.0.1:8000/admin/**.

### 3.10 Run the test suite
```bash
python manage.py test
```

---

## 4. How the 4-step flow works in the app

1. **Enter Your Details** (`/bookings/new/`) — client fills in date, addresses, property type, bedrooms,
   service type, crew size, etc. Saved as a `Booking` in `draft` status.
2. **Get Your Price** (`/bookings/<id>/quote/`) — client selects one or two `MovingCompany` records; the
   app instantly computes a guaranteed price per company (`app/pricing.py`) and lets them pick one.
3. **Book Your Move** — selecting a company sets `Booking.company`, `Booking.price`, and moves status to
   `confirmed`.
4. **Track and Communicate** (`/bookings/<id>/`) — shows live status (updatable by the assigned driver or
   an admin) plus a simple message thread between the client and their mover.

Two extra objectives are implemented as their own screens, linked from the booking detail page:
- **Inventory checklist** — `/bookings/<id>/inventory/`
- **Moving-day timeline / task planner** — `/bookings/<id>/timeline/`

---

## 5. Roles: Admin / Driver / Client

Every user has a `Profile` with a `role` (`client`, `driver`, or `admin`), chosen at sign-up.

- **Client** — books moves, gets quotes, manages inventory/timeline, messages their mover, pays.
- **Driver** — sees only bookings assigned to them (`/bookings/`), can update a booking's status and
  message the client.
- **Admin** — sees every booking, plus full access to the Django admin panel (`/admin/`) to manage
  moving companies, assign drivers to bookings, and oversee all data. To make a user an admin with
  panel access, either check "staff status" for them in `/admin/` or set `role=admin` and
  `is_staff=True` via `createsuperuser`/`seed_demo_data`.

---

## 6. M-Pesa (Daraja) setup — sorting the secrets properly

The original project had hardcoded API keys and made a live network call the moment the app started up
(which could crash the whole server). This version:
- Reads all M-Pesa credentials from environment variables only (`app/mpesa.py` + `Sender/settings.py`).
- Never calls the Daraja API at import time — only when a customer actually clicks "Pay Now".

To enable real payments:
1. Create a free account at https://developer.safaricom.co.ke and create an app to get sandbox
   `Consumer Key` / `Consumer Secret`.
2. Use the published sandbox `Shortcode` (174379) and `Passkey` for testing, listed in Safaricom's own
   Daraja documentation.
3. Fill these into your `.env`:
   ```
   MPESA_ENV=sandbox
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=174379
   MPESA_PASSKEY=...
   MPESA_CALLBACK_URL=https://<your-public-domain>/payments/callback/
   ```
   Note: Safaricom's servers must be able to reach `MPESA_CALLBACK_URL` over the public internet, so
   this only works once deployed (or via a tunnel like `ngrok` during local testing).
4. When you're ready to go live, set `MPESA_ENV=production`, and swap in your production shortcode,
   passkey, and credentials from Safaricom — never commit these to git.

---

## 7. Deployment

### General checklist for any host
1. Set real environment variables (never commit `.env`):
   - `DEBUG=False`
   - `SECRET_KEY` — a long, random value
   - `ALLOWED_HOSTS` — your real domain(s), comma-separated
   - `DATABASE_URL` — a managed Postgres connection string (recommended for production; SQLite is
     fine for demos but not for concurrent production traffic)
   - `MPESA_*` — your real Daraja credentials (see section 6)
2. Install dependencies: `pip install -r requirements.txt`
3. Collect static files: `python manage.py collectstatic --noinput`
4. Run migrations: `python manage.py migrate`
5. Create your real admin account: `python manage.py createsuperuser`
6. Serve with a production WSGI server, e.g. `gunicorn Sender.wsgi:application`

### Deploying to Vercel (matches the included `vercel.json`)
1. Push the project to a GitHub repository.
2. Import the repo in the Vercel dashboard, or run `vercel` from the project root with the Vercel CLI.
3. In the Vercel project's **Settings → Environment Variables**, add every variable from `.env.example`
   with real production values (`DEBUG=False`, a strong `SECRET_KEY`, your real `ALLOWED_HOSTS`, and
   your M-Pesa production credentials).
4. Vercel will build using `Sender/wsgi.py` (already configured in `vercel.json`).
5. Because serverless deployments don't have a persistent disk, use a managed Postgres database (e.g.
   Neon, Supabase, or Vercel Postgres) via `DATABASE_URL` rather than SQLite in production.
6. After the first deploy, run migrations against your production database from your local machine by
   temporarily pointing `DATABASE_URL` at it: `python manage.py migrate`.

### Deploying to a traditional host (Railway, Render, a VPS, etc.)
1. Set the same environment variables as above.
2. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start command: `gunicorn Sender.wsgi:application --bind 0.0.0.0:$PORT`

---

## 8. Secrets — what changed and why

| Secret | Old behaviour | New behaviour |
|---|---|---|
| Django `SECRET_KEY` | Hardcoded in `settings.py`, committed to git | Read from `SECRET_KEY` env var; only a clearly-labeled insecure fallback is used, and only in `DEBUG` mode |
| M-Pesa consumer key/secret | Hardcoded in `credentials.py` **and** duplicated in `views.py` | Read once from env vars in `Sender/settings.py`, used only via `app/mpesa.py` |
| User passwords | Stored in plain text in a custom `User` model | Hashed automatically by Django's built-in `auth.User` (PBKDF2 by default) |
| `.env` file | Did not exist | `.env.example` provided as a template; real `.env` is git-ignored |

**Never commit your real `.env` file.** It's already listed in `.gitignore`.

---

## 9. What was fixed vs. the original project

- **Broken authentication**: the original code defined a custom `User` model that silently shadowed
  Django's real `django.contrib.auth.models.User`, so `login()` never actually logged anyone in and
  `@login_required` could never pass. Now uses Django's real, secure auth system throughout.
- **Plain-text passwords**: replaced with Django's built-in password hashing.
- **Startup crash risk**: the old `credentials.py` made a live HTTP request to Safaricom at import time,
  which could crash the entire app on boot. M-Pesa calls are now 100% lazy (only triggered by an actual
  "Pay Now" click).
- **Hardcoded secrets**: all moved to environment variables.
- **Broken static file config**: `STATICFILES_DIRS` pointed at the project root instead of the static
  folder; fixed and using `whitenoise` for production static serving.
- **`request` variable shadowing bug** in the old `stk()` view: removed.
- **No M-Pesa callback handling**: added a real `/payments/callback/` endpoint that updates a `Payment`
  record tied to its `Booking`.
- **Missing objectives**: added `InventoryItem` (belongings checklist), `MoveTask` (moving-day planning
  timeline), `MovingCompany` (mover discovery/comparison), and `Profile.role` (Admin/Driver/Client menus)
  — none of which existed in the original models.
- **Missing steps in the 4-step flow**: added an actual "Get Your Price" comparison/quote step and a
  "Track & Communicate" message thread; both were absent before.
- **Frontend**: replaced 6+ inconsistent, per-page CSS files and heavy inline `style="..."` attributes
  throughout every template with one unified, token-based design system (`static/css/styles.css`),
  while keeping every original image file exactly as provided.

---

## 10. Notes on the images

All images in `static/images/` are your original files, unmodified. A few filenames that contained
spaces/parentheses were renamed for URL-safety (e.g. `images (2).jpeg` → `images-2-.jpeg`) — only the
filename changed, never the image content.
