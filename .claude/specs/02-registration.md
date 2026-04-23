# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account.
The POST handler validates the form, checks for duplicate emails, hashes the
password, inserts the user, stores their `user_id` in the session, and
redirects to the dashboard (stub for now). This is the first authenticated
surface in the app and establishes the session pattern every later step reuses.

## Depends on
- Step 01: Database setup (`users` table, `get_db()`)

## Routes
- `GET  /register` — render registration form — public (already exists, expand to handle POST)
- `POST /register` — process form submission, insert user, set session — public

## Database changes
No new tables or columns. Relies on the existing `users` table:
- `id`, `name`, `email`, `password_hash`, `created_at`

The UNIQUE constraint on `email` is already in place — the route must catch
the IntegrityError and surface a user-friendly message.

## Templates
- **Modify:** `templates/register.html`
  - Add `method="POST"` and `action="/register"` to the `<form>` tag
  - Add `name` input field (full name)
  - Ensure `email` and `password` inputs have correct `name` attributes
  - Display flash messages (errors and success) at the top of the form
  - Add a "Already have an account? Log in" link pointing to `/login`

## Files to change
- `app.py` — convert `/register` to accept GET and POST; add session secret key; import `session`, `redirect`, `url_for`, `flash`, `request` from Flask
- `templates/register.html` — wire up form and flash message display
- `database/db.py` — no changes needed

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug.security.generate_password_hash` is already
available via Flask's dependency on Werkzeug.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use string formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Set `app.secret_key` from an env variable with a hard-coded fallback for dev: `os.environ.get("SECRET_KEY", "dev-secret-change-me")`
- On duplicate email, catch `sqlite3.IntegrityError` and flash a specific error: "An account with that email already exists."
- On any other DB error, flash a generic error and log it
- After successful registration, store `session["user_id"]` and redirect to `/` (landing) until the dashboard exists
- Validate server-side: name non-empty, email non-empty, password at least 8 characters — flash a specific message for each failure
- Do not expose raw exception messages to the user

## Definition of done
- [ ] `GET /register` renders the form with no errors
- [ ] Submitting with all valid fields creates a new row in `users` with a hashed password
- [ ] Submitting with a duplicate email shows "An account with that email already exists." without crashing
- [ ] Submitting with an empty name shows a validation error
- [ ] Submitting with a password shorter than 8 characters shows a validation error
- [ ] After successful registration `session["user_id"]` is set
- [ ] After successful registration the user is redirected (not shown a blank page)
- [ ] Flash messages are visible on the form page
- [ ] Re-running `init_db()` and `seed_db()` on app restart does not break registration
