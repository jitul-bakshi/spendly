# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

```bash
source venv/bin/activate
python3 app.py          # runs on http://localhost:5001
```

## Running tests

```bash
source venv/bin/activate
pytest                  # all tests
pytest tests/test_foo.py::test_name   # single test
```

## Architecture

This is a **Flask + SQLite** expense tracking web app. There is no frontend framework — all UI is server-rendered Jinja2 templates with plain CSS and vanilla JS.

**Entry point:** `app.py` — defines the Flask app and all routes. All route functions live here (no blueprints).

**Database layer:** `database/db.py` — three functions students implement:
- `get_db()` — returns a SQLite connection (row_factory set, foreign keys enabled)
- `init_db()` — creates tables with `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — inserts sample data

The database file is SQLite, stored locally. `database/__init__.py` is intentionally empty.

**Templates:** all in `templates/`, extend `templates/base.html`. The base template includes the navbar, footer (with Terms/Privacy links), and loads `static/css/style.css` and `static/js/main.js`. Per-page extra CSS/JS goes in `{% block head %}` and `{% block scripts %}`.

**Styling:** `static/css/style.css` is the global stylesheet with CSS custom properties defined in `:root`. The landing page has its own `static/css/landing.css` (loaded via `{% block head %}` in `landing.html`) to keep landing-specific styles isolated.

**JS:** `static/js/main.js` is the global JS file (currently a stub). Page-specific JS is inlined in `{% block scripts %}` blocks — see the YouTube modal in `landing.html` for the pattern.

## Routes

| Method | Path | Template | Notes |
|--------|------|----------|-------|
| GET | `/` | `landing.html` | Public landing page |
| GET/POST | `/register` | `register.html` | Auth — POST not yet implemented |
| GET/POST | `/login` | `login.html` | Auth — POST not yet implemented |
| GET | `/logout` | — | Stub |
| GET | `/terms` | `terms.html` | Static legal page |
| GET | `/privacy` | `privacy.html` | Static legal page |
| GET | `/profile` | — | Stub |
| GET | `/expenses/add` | — | Stub |
| GET/POST | `/expenses/<id>/edit` | — | Stub |
| GET/POST | `/expenses/<id>/delete` | — | Stub |

Stub routes return plain strings and are placeholders for future steps.

## Design tokens

All colours, fonts, and spacing are defined as CSS variables in `:root` in `style.css`. Key ones:

- `--ink` / `--ink-muted` / `--ink-faint` — text hierarchy
- `--accent` (`#1a472a`) — dark green, used for brand accents
- `--paper` / `--paper-card` — background surfaces
- `--font-display` — DM Serif Display (headings)
- `--font-body` — DM Sans (everything else)
