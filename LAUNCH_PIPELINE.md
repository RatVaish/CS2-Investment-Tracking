# Floatbase — Pre-Launch Pipeline
> Target launch: **1 May 2026**
> Update this file as tasks are completed.

---

## ✅ Completed

- [x] V4 normalized database schema (18 tables)
- [x] Google OAuth + Steam OpenID auth
- [x] Portfolio CRUD (investments, sell, delete)
- [x] CSFloat + Buff163 + Steam price pipeline
- [x] Steam price history charts (OHLV candles)
- [x] Backfill queue (on-demand Steam history fetch)
- [x] Rolling dashboard (1M/3M/1Y/ALL timeframes)
- [x] Trade markers on investment detail chart
- [x] DCA positions + weighted avg entry line
- [x] Stripe freemium — free tier (10 investments) + Pro ($6/mo, $50/yr)
- [x] Stripe webhook → tier flip working end to end (live mode verified ✓)
- [x] Paywall modal
- [x] CSV export (Pro)
- [x] Spreadsheet import — CSV, Excel, TSV (Pro)
- [x] Steam inventory import removed from Pro (deferred to post-launch)
- [x] Cloudflare Tunnel (floatbase.app + api.floatbase.app)
- [x] Telegram health alerts (Steam cookie expiry)
- [x] Legal pages (Terms, Privacy, Cookies)
- [x] Branding (Floatbase throughout, favicon, meta tags)
- [x] Entry line always visible on chart (green dashed, all timeframes)
- [x] Entry line quantity + price label
- [x] Pie chart tooltip readable (white text)
- [x] `_maybe_queue_backfill` NameError fixed
- [x] `held` undefined white screen on AddInvestmentForm fixed
- [x] Snapshot backfill on investment creation (price history → snapshots)
- [x] Gap check on dashboard load (fills missing snapshots for existing users)

---

## 🔴 Must Have Before Launch

### Email Verification
Needed to confirm emails are real, prevent fake accounts, and enable
password reset. Without this anyone can register with a fake email.
- [ ] Backend: generate signed verification token on registration
- [ ] Backend: send verification email (link with token)
- [ ] Backend: `/auth/verify-email?token=...` endpoint that marks `email_verified=True`
- [ ] Backend: resend verification endpoint
- [ ] Frontend: "Check your email" screen shown after registration
- [ ] Frontend: verified badge / warning banner if unverified
- [ ] Frontend: resend button if not received
- [ ] Gate: decide what unverified users can/can't do (suggest: can browse, can't add investments)
- [ ] Email provider: set up SendGrid or Resend (free tiers sufficient for launch)

### Price Alerts + Notifications
The only advertised Pro feature that is completely unbuilt (schema exists, zero backend logic).
- [ ] Backend: CRUD endpoints (create, list, delete alerts)
- [ ] Backend: Scheduler job — check alerts after every CSFloat/Buff price update
- [ ] Backend: Write to `notifications` table when alert triggers, mark alert inactive
- [ ] Frontend: Bell icon in Navbar with unread badge count
- [ ] Frontend: Notification inbox dropdown (mark as read, link to item)
- [ ] Frontend: Price alert creation UI on investment detail page

### Add Investment Form Rework
Current form needs a full review and polish pass before launch.
- [ ] Audit current form fields and flow end to end
- [ ] Review item search UX (ItemSearchSelect component)
- [ ] Review PurchaseDatePicker (Exact vs Approx mode)
- [ ] Fix any remaining edge cases

### Import Testing
Backend is built, needs real end-to-end verification.
- [ ] CSV import — happy path, malformed CSV, items not in DB, free tier limit mid-import
- [ ] CSV/Excel/TSV import — happy path, malformed file, items not in DB, free tier mid-import

---

## 🟡 Should Have Before Launch (Tier 3)

### Portfolio vs Market Benchmark
Most compelling Pro upgrade reason — "your portfolio +12% vs CS2 index +3%".
- [ ] Backend: populate `market_benchmarks` table from price_history aggregations
- [ ] Backend: scheduler job — daily benchmark calculation (top 100 traded items)
- [ ] Frontend: benchmark overlay line on dashboard portfolio chart
- [ ] Frontend: stat card showing portfolio vs index delta

### Watchlist UI
DB model + relationships exist, zero frontend.
- [ ] Backend: CRUD endpoints (add, list, remove)
- [ ] Frontend: Watchlist tab in dashboard
- [ ] Frontend: item search → add to watchlist
- [ ] Frontend: current prices shown per watchlist item
- [ ] Frontend: set price alert directly from watchlist row

### Investment Tags UI
DB model exists, zero frontend. Quick win.
- [ ] Backend: CRUD endpoints (add/remove tags per investment)
- [ ] Frontend: tag chips on investment rows in portfolio table
- [ ] Frontend: add/remove tags on investment detail page
- [ ] Frontend: filter portfolio by tag

---

## 🟢 Post-Launch Roadmap (v1.1+)

### Chart Upgrade (lightweight-charts)
Replace Recharts with TradingView's lightweight-charts.
- All data loaded upfront, zoom/pan between resolutions
- Smooth animation between timeframes
- Estimated: half day rebuild of InvestmentDetail chart section

### Public Trader Profiles
Opt-in shareable profile URL (`floatbase.app/u/username`).
- ROI, best trades, current watchlist visible
- Viral acquisition loop via Reddit/Discord sharing

### Market Pulse
Aggregated anonymous market intelligence from price history.
- "This week: AK-47s +5%, Cases flat, Knives -2%"
- Content marketing engine, no user data needed

### Email / Telegram Alert Delivery
Currently alerts only show in-app. Add:
- Email on trigger (SendGrid/Resend)
- Optional Telegram bot per user

### AI Trade Guidance Agent
6–10 months post-launch. Pro-only.

### CS2 News Feed
Aggregate from Reddit, community blogs, filter by item type.

### Steam Inventory Import
Deep Steam integration — float values, sticker data, purchase history.
Likely requires a browser extension (similar to TradeUpSpy model).
- [ ] Research browser extension approach
- [ ] Investigate Steam API capabilities and limits

### Sticker Craft Calculator
Craft cost vs expected skin value uplift.

---


---

## 🎨 Pre-Launch Polish Pass

A full sweep of the product before go-live. Do this last, after all features are built.

### UI & Copy
- [ ] Full walkthrough of every page — spacing, alignment, colour consistency
- [ ] Review all placeholder text, empty states, and loading states
- [ ] Check all error messages are user-friendly (no raw API errors shown)
- [ ] Mobile responsiveness check on all pages
- [ ] Consistent font sizing and weight hierarchy throughout
- [ ] Review all button labels and CTA copy for clarity

### Branding & Identity
- [ ] Design and implement the Floatbase logo (currently text-only)
- [ ] Update favicon to use final logo
- [ ] Apply logo consistently across Navbar, Landing, emails, and meta tags
- [ ] Review og:image / social preview card (shown when link is shared on Discord/Reddit)

### Landing Page
- [ ] Full rewrite of hero headline and subheading — sharp, specific, CS2-trader-focused
- [ ] Review feature cards — copy, icons, ordering
- [ ] Review pricing section — make Pro value obvious
- [ ] Add a screenshot or short demo video/gif of the actual app
- [ ] Review footer links and social links

### Legal Documents
- [ ] Re-read Terms of Service for any gaps post-feature additions (imports, alerts, Stripe)
- [ ] Re-read Privacy Policy — ensure Stripe data handling, email storage, and Steam data are covered
- [ ] Check Cookie Policy reflects actual cookies in use
- [ ] Ensure GDPR data export / deletion flow works end to end

---

## 📣 Update Announcements (Post-Launch Infrastructure)

Multi-pane update popup shown on login when a user has missed announcements.
Similar to Axiom's update announcements — each update has a title, description, and media.
If a user misses 2-3 updates, all are shown as panes in a single modal on next login.

### Database
- [ ] New `announcements` table: `id`, `title`, `body`, `media_url`, `media_type` (image/video), `published_at`, `is_active`
- [ ] New `user_announcement_views` table: `user_id`, `announcement_id`, `viewed_at` — tracks which announcements each user has seen
- [ ] Alembic migration for both tables

### Backend
- [ ] `GET /announcements/unseen` — returns all active announcements the current user hasn't seen yet, ordered by `published_at`
- [ ] `POST /announcements/mark-seen` — accepts list of announcement IDs, writes to `user_announcement_views`
- [ ] Admin-only `POST /announcements` endpoint to publish new announcements (or just insert directly via DB for now)

### Frontend
- [ ] `AnnouncementModal` component — multi-pane modal, one pane per unseen announcement
- [ ] Each pane: title, description text, image or video, prev/next navigation, "Got it" on last pane
- [ ] Dot indicators showing position (● ○ ○) across panes
- [ ] Triggered on dashboard load — fetch unseen announcements, show modal if any exist
- [ ] On close / "Got it": POST mark-seen for all shown announcements
- [ ] Smooth pane transition animation

### Content
- [ ] Write announcement for launch itself ("Welcome to Floatbase 🎉")
- [ ] Establish a cadence — aim for one announcement per meaningful update
- [ ] Keep announcements concise — one feature per pane, screenshot or short gif preferred

---

## Notes
- Stripe is in **live mode** — real cards will be charged
- Steam cookie (`STEAM_LOGIN_SECURE`) expires periodically — Telegram bot alerts on expiry
- `docker compose up --build -d` to deploy after any change
- Always `git pull` on server before rebuilding
