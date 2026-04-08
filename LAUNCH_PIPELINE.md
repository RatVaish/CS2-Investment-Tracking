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
- [x] Steam inventory import (Pro)
- [x] Cloudflare Tunnel (floatbase.app + api.floatbase.app)
- [x] Telegram health alerts (Steam cookie expiry)
- [x] Legal pages (Terms, Privacy, Cookies)
- [x] Branding (Floatbase throughout, favicon, meta tags)
- [x] Entry line always visible on chart (green dashed, all timeframes)
- [x] Entry line quantity + price label
- [x] Pie chart tooltip readable (white text)
- [x] Dashboard chart shows cost basis → current value for new users (no snapshot dependency)
- [x] `_maybe_queue_backfill` NameError fixed
- [x] `held` undefined white screen on AddInvestmentForm fixed

---

## 🔴 Must Have Before Launch

### Price Alerts + Notifications
The only advertised Pro feature that is completely unbuilt (schema exists, zero backend logic).
- [ ] Backend: CRUD endpoints (create, list, delete alerts)
- [ ] Backend: Scheduler job — check alerts after every CSFloat/Buff price update
- [ ] Backend: Write to `notifications` table when alert triggers, mark alert inactive
- [ ] Frontend: Bell icon in Navbar with unread badge count
- [ ] Frontend: Notification inbox dropdown (mark as read, link to item)
- [ ] Frontend: Price alert creation UI on investment detail page + watchlist

### Add Investment Form Rework
Current form has UX issues — needs a full review and polish pass.
- [ ] Audit current form fields and flow
- [ ] Review item search UX (ItemSearchSelect component)
- [ ] Review PurchaseDatePicker (Exact vs Approx mode)
- [ ] Fix any remaining edge cases

### Import Testing
Backend is built, needs real end-to-end verification.
- [ ] CSV import — test happy path, malformed CSV, items not in DB, free tier limit mid-import
- [ ] Steam import — test with public inventory, private inventory error, already-imported items

---

## 🟡 Should Have Before Launch (Tier 3)

### Portfolio vs Market Benchmark
Most compelling Pro upgrade reason — "your portfolio +12% vs CS2 index +3%".
- [ ] Backend: Populate `market_benchmarks` table from price_history aggregations
- [ ] Backend: Scheduler job — daily benchmark calculation (top 100 traded items)
- [ ] Frontend: Benchmark overlay line on dashboard portfolio chart
- [ ] Frontend: Stat card showing portfolio vs index delta

### Watchlist UI
DB model + relationships exist, zero frontend.
- [ ] Backend: CRUD endpoints (add, list, remove watchlist items)
- [ ] Frontend: Watchlist tab in dashboard
- [ ] Frontend: Item search → add to watchlist
- [ ] Frontend: Current prices shown per watchlist item
- [ ] Frontend: Set price alert directly from watchlist row

### Investment Tags UI
DB model exists, zero frontend. Quick win.
- [ ] Backend: CRUD endpoints (add/remove tags per investment)
- [ ] Frontend: Tag chips on investment rows in portfolio table
- [ ] Frontend: Add/remove tags on investment detail page
- [ ] Frontend: Filter portfolio by tag

### Notification Inbox
Coupled with Price Alerts above.
- [ ] Already captured under Price Alerts section

---

## 🟢 Post-Launch Roadmap (v1.1+)

### Chart Upgrade (lightweight-charts)
Replace Recharts with TradingView's lightweight-charts library.
- All data loaded upfront, zoom/pan between resolutions
- Smooth animation between timeframes
- Professional trading terminal feel
- Estimated: half day rebuild of InvestmentDetail chart section

### Public Trader Profiles
Opt-in shareable profile URL (`floatbase.app/u/username`).
- ROI performance, best trades, current watchlist (opt-in visibility)
- Viral acquisition loop — users share on Reddit/Discord
- Follow traders, get notified of moves (later)

### Market Pulse
Aggregated anonymous market intelligence from price history data.
- "This week: AK-47 category +5%, Cases flat, Knives -2%"
- No user data needed — purely from item price history
- Content marketing engine for Reddit/Discord

### Email / Telegram Alert Delivery
Currently alerts only show in-app notification inbox.
- Email on trigger (via SendGrid or Resend)
- Optional Telegram bot integration

### AI Trade Guidance Agent
6–10 months post-launch.
- Analyses portfolio composition, market trends, suggests entries/exits
- Pro-only feature

### CS2 News Feed
Aggregate from multiple CS2 trading sources.
- Reddit r/csgomarketforum, community blogs
- Filter by item type / collection

### Sticker Craft Calculator
Given sticker prices, calculate craft cost vs expected skin value uplift.

---

## Notes
- Stripe is in **live mode** — real cards will be charged
- Steam cookie (`STEAM_LOGIN_SECURE`) expires periodically — Telegram bot alerts on expiry
- `docker compose up --build -d` to deploy after any change
- Always `git pull` on server before rebuilding
