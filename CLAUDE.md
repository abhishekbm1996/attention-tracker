# Drass - Attention Tracker

## Architecture
- **Frontend**: Vanilla HTML/CSS/JS (PWA) with service worker caching
- **Backend**: Python FastAPI (server/main.py, server/database.py)
- **Database**: PostgreSQL (Supabase, Mumbai region) in production, SQLite locally
- **Hosting**: Vercel serverless, function region set to `bom1` (Mumbai)
- **Auth**: HTTP Basic Auth (env vars BASIC_AUTH_USER, BASIC_AUTH_PASSWORD)
- **Entrypoint**: index.py (Vercel), server/main.py (FastAPI app)

## Key Files
- `server/main.py` — API routes (sessions, distractions, stats, summary)
- `server/database.py` — All DB logic, connection caching, CRUD
- `server/models.py` — Pydantic response models
- `static/app.js` — Frontend with optimistic UI updates
- `static/stars.js` — Canvas starfield with twinkling stars and milky way band
- `static/style.css` — Ladakhi night sky theme (glassmorphism, icy blues, amber distraction)
- `static/service-worker.js` — PWA caching (v6), API calls bypass cache
- `vercel.json` — Vercel config (fastapi framework, bom1 region)
- `tests/test_api.py` — 16 API tests, run with `python3 -m pytest tests/ -v`

## Database
- **Tables**: sessions (id, started_at, ended_at, name), distractions (id, session_id, created_at)
- **Indexes**: idx_sessions_started_at, idx_sessions_ended_at, idx_distractions_session_id
- **Connection caching**: Module-level `_cached_pg_conn` reused across warm Vercel invocations
- **Connection release**: `_release(conn)` only closes SQLite; PG connections stay cached
- **TCP keepalives** enabled on PG connections (idle=30s, interval=10s, count=5)
- Timestamps stored as ISO 8601 UTC strings (TEXT columns)
- IST timezone (UTC+5:30) used for "today" boundaries in stats
- **Production data was wiped clean** on 2026-02-15 (was 36 sessions, 90 distractions of test data)

## Performance Optimizations (Feb 2025 session)
### Problem: API responses were 1-3s
### Root causes found and fixed:
1. **No DB indexes** → Added indexes on started_at, ended_at, session_id
2. **Multiple DB connections per request** (2-4 each) → Consolidated to single-connection functions:
   - `validate_and_add_distraction()` — validates + inserts in 1 connection
   - `end_session_full()` — validates + ends + computes summary in 1 connection
   - `get_active_session()` — uses LEFT JOIN instead of 2 queries
3. **N+1 query in get_stats()** (50+ queries) → Batch fetch all sessions + distractions in 2 queries, bucket by IST day in Python
4. **New PG connection every request** (~1.5-2s handshake) → Module-level cached connection
5. **SELECT 1 health check on every request** → Replaced with local `conn.closed` check
6. **Function region mismatch** — Function ran in US East (iad1), DB in Mumbai → Set `"regions": ["bom1"]` in vercel.json
### Result: 2-3s → ~150ms (warm), ~800ms (cold)

## UI Redesign (Feb 2026 session) — "Ladakhi Night Sky" theme
- **Background**: Deep navy (#050b1a) with canvas starfield (twinkling stars clustered along diagonal milky way band) + CSS nebula glow
- **Glassmorphism**: All cards use `backdrop-filter: blur`, translucent backgrounds, subtle borders
- **Colors**: Icy blue accent (#6cb4f7), warm amber distraction button (#e8934a — warmth breaking the cold)
- **Typography**: Inter font from Google Fonts, gradient shimmer on title
- **Animations**: View fade-in + slide-up transitions, breathing glow on timer, title shimmer
- **Responsive**: Trend rows and stat cards stack vertically on mobile (<480px)
- **Service worker**: Bumped to v6 with stars.js in precache list
- **Favicon**: Updated to "D" with icy blue on navy background

## Frontend Patterns
- **Optimistic UI**: Start session, distraction count, end session all update UI instantly before API returns
- **Session caching**: localStorage (`drass_active_session`) restores state on page load, validated with API in background
- **Fire-and-forget**: Distraction API calls don't block UI; revert count on error
- **Session promise**: `sessionPromise` tracks pending session creation so distractions/end can wait if needed

## API Endpoints
- `POST /api/sessions` — Start session (optional JSON body: `{"name": "..."}`)

- `GET /api/sessions/active` — Get active session with distraction count
- `PATCH /api/sessions/{id}` — End session (returns full summary)
- `GET /api/sessions/{id}/summary` — Get summary for ended session
- `POST /api/sessions/{id}/distractions` — Log distraction
- `GET /api/stats` — Today stats + 7-day trend

## Commands
- Run tests: `python3 -m pytest tests/ -v`
- Local dev: `uvicorn server.main:app --reload`

## Credentials (production)
- Site: https://drass-attention-tracker.vercel.app
- Username: abhishek / Password: xijtoj-8Jownu-zojnaz
- Production Supabase project ref: `earnirhvqaqvexpfwxfp`

## Vercel
- Team ID: `team_JAUH3plaCLIihIS3nMAAlg1H`
- Project ID: `prj_Vr1wNWB21Pn1HCm97li4ma4g4BU4`
- Production domain: `drass-attention-tracker.vercel.app`

## MCP
- **Vercel MCP**: Configured (http transport, https://mcp.vercel.com)
- **Supabase MCP**: Configured in `.mcp.json` (project-scoped, project-ref=earnirhvqaqvexpfwxfp)
- `.mcp.json` is in `.gitignore` (contains access token)

## Staging Environment
- **Staging Supabase project**: `outrxmhsicmdwcqcdklo` (Mumbai region, free tier)
- **Staging DB URL**: `postgresql://postgres.outrxmhsicmdwcqcdklo:...@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`
- **How it works**: Push to any non-main branch → Vercel creates a preview deployment using the Preview-scoped `DATABASE_POSTGRES_URL` (staging DB). Main branch deploys to production with its own Production-scoped `DATABASE_POSTGRES_URL`.
- **Vercel env vars**: Two `DATABASE_POSTGRES_URL` entries — one scoped to Production, one to Preview. `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` are All Environments.
- **Important**: Connection string MUST end with `/postgres` (database name). Missing it causes `database "postgres.{ref}" does not exist` errors.
- **Test branch**: `test-staging` was used to verify the setup (can be deleted).

## Session Naming (Feb 2026)
- Optional text input on landing view before "Start Session" button
- Name stored in `sessions.name` column (nullable TEXT), added via `init_db()` migration
- Displayed as accent-colored label above timer during active session
- Included in all session API responses (`SessionResponse`, `ActiveSessionResponse`, `SessionEndResponse`)
- Cached in localStorage alongside session data
- Backward compatible: sessions without a name work exactly as before

## TODO (next session)
1. **Motivational voice on distraction button**: Replace the beep with a short spoken nudge (e.g. "stay focused") — explore Web Speech API or short audio clips
2. **Clean up test-staging branch**: Delete the `test-staging` branch from GitHub
