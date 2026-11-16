# BuildBack — CLAUDE.md

> Documentation for the BuildBack surplus construction materials marketplace.
> Phase 1: Local marketplace (20 km) with transport cost & savings calculator.

---

## Quick Start

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Configure .env (see .env.example)
cp .env.example .env
# Edit .env with MySQL, Google Maps, Cloudinary credentials

# 3. Run migrations
python manage.py migrate

# 4. Start server
python manage.py runserver
# → http://127.0.0.1:8000/
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5.1 (Python 3.12) |
| Database | MySQL (mysqlclient) — SQLite for tests |
| Image Storage | Cloudinary (URLs stored in MySQL) |
| Maps | Google Maps JS API (Places, Distance Matrix) |
| Frontend | Vanilla HTML/CSS/JS (Django templates) |
| Testing | pytest-django (4 unit tests for calculator) |

---

## Project Structure

```
miniproject/
├── manage.py
├── requirements.txt
├── .env                    # Local secrets (not committed)
├── .env.example            # Template for .env
├── CLAUDE.md               # This file
├── buildback/              # Django project config
│   ├── __init__.py
│   ├── settings.py         # All settings (MySQL, Cloudinary, test DB)
│   ├── urls.py             # Root URLconf
│   ├── context_processors.py  # google_maps_key for templates
│   └── wsgi.py
├── marketplace/            # Main app
│   ├── __init__.py
│   ├── models.py           # User, Material, MaterialImage, Location, DistanceCache
│   ├── views.py            # All HTML views (home, browse, sell, detail, my_listings, auth)
│   ├── views_api.py        # JSON endpoints (calculator/estimate/)
│   ├── forms.py            # RegistrationForm, MaterialForm, LocationForm, ImageUploadForm
│   ├── services.py         # Haversine, Distance Matrix (cached), estimate_savings()
│   ├── tests.py            # CalculatorTests (4 tests)
│   ├── urls.py             # App routes
│   ├── admin.py
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_add_indexes.py
├── static/
│   ├── css/styles.css      # Design system (1200+ lines)
│   └── js/
│       ├── main.js         # Header, mobile menu, count-up, scroll reveal
│       ├── browse.js       # AJAX filter/search/sort/pagination, geolocation
│       ├── sell.js         # Drag-drop upload, Google Maps picker
│       ├── calculator.js   # Vehicle defaults, API calc, verdict badge
│       └── maps.js         # Detail map, gallery thumbnails
└── templates/
    ├── base.html           # Layout, header, footer, modals
    ├── home.html           # Hero, featured, categories, how-it-works, CTA
    ├── browse.html         # Filter bar, grid, skeletons, pagination
    ├── sell.html           # 3-section form (details, photos, location)
    ├── detail.html         # Gallery, details, seller, map, calculator
    ├── my_listings.html    # Table with edit/mark-sold/delete
    ├── login.html
    ├── register.html
    └── partials/
        ├── listing_card.html
        └── delete_confirm.html
```

---

## Data Models

### User (Custom, `AUTH_USER_MODEL = 'marketplace.User'`)
- `role`: `buyer` | `seller`
- `phone`: CharField(15, blank)

### Material
- `seller` → User (FK, related_name=`listings`)
- `name`, `category` (tiles/cement/bricks/steel/pipes/other, **indexed**)
- `quantity` (Decimal), `unit` (CharField)
- `original_price`, `selling_price` (Decimal)
- `condition`: `unused` | `opened` | `used`
- `status`: `available` | `sold` (**indexed**)
- `created_at` (auto_now_add)
- **Composite index**: `(category, status)`

### MaterialImage
- `material` → Material (FK, related_name=`images`)
- `image_url` (URLField, Cloudinary)
- `position` (IntegerField, 0 = main)

### Location
- `owner_type`: `'user'` | `'material'`
- `owner_id`: Integer
- `lat`, `lng` (Decimal 9,6, **indexed**)
- `address` (TextField)

### DistanceCache
- `origin_lat/lng`, `dest_lat/lng` (rounded to 4dp ≈ 11m)
- `km` (Decimal), `minutes` (Integer)
- `expires_at` (DateTime, **indexed**, 7-day TTL)
- **Composite index**: `(origin_lat, origin_lng, dest_lat, dest_lng)`

---

## Key Algorithms

### 20 km Search (`views.py::browse`)
1. **Bounding box** (fast, DB-level): ~0.18° lat, 0.18°/cos(lat) lng
2. **Haversine** (services.py) — straight-line fallback
3. **Google Distance Matrix** (server-side only) — road distance for top results
4. **Cache**: `DistanceCache` model, 7-day TTL, rounded coords

### Savings Calculator (`services.py::estimate_savings`)
Pure Python, unit-tested, no external deps.

```python
params = {
    'quantity': 100,
    'vehicle_rate': 10,      # ₹/km
    'min_fare': 50,          # ₹
    'selling_price': 5,      # ₹/unit
    'new_market_price': 8,   # ₹/unit
    'distance_km': 10
}
# transport = max(min_fare, distance_km * vehicle_rate)
# material_cost = quantity * selling_price
# total = material_cost + transport
# savings = (quantity * new_market_price) - total
# verdict = "Worth buying" if savings > 0 else "Not worth it"
```

**Endpoint**: `POST /calculator/estimate/` (JSON in/out)
- Called via fetch from `detail.html` calculator panel
- Uses buyer location (GPS) + seller location (from listing)

---

## Frontend Architecture

### CSS Design System (`static/css/styles.css`)
- **Variables**: `--bg`, `--card`, `--cream`, `--gold`, `--text`, `--muted`, `--line`, `--success`, `--danger`
- **Fonts**: Cormorant Garamond (headings), Inter (body)
- **Breakpoints**: 480 / 768 / 1024
- **Themes**: Dark (app pages), Cream (alternating sections on home)
- **Components**: Cards, badges, buttons, forms, tables, modals, skeletons

### JavaScript Modules (ES5, IIFE, no build step)
| File | Responsibility |
|------|----------------|
| `main.js` | Header scroll, hamburger menu, user dropdown, count-up animation, IntersectionObserver reveal, toast utility |
| `browse.js` | Debounced (300ms) fetch for search/category/sort/pagination, geolocation button, skeleton loaders |
| `sell.js` | Drag-drop upload (5 files, 5MB, JPG/PNG/WebP), preview thumbnails, Google Maps autocomplete + draggable pin + GPS + reverse geocode |
| `calculator.js` | Vehicle select → auto-fills rate/min-fare, local fallback calc, POST to `/calculator/estimate/`, renders results + verdict badge |
| `maps.js` | Detail page map (seller marker + buyer marker), gallery thumbnail switching |

---

## Environment Variables (`.env`)

```env
DEBUG=True
SECRET_KEY=your-django-secret-key
DATABASE_URL=mysql://user:pass@localhost:3306/buildback
CLOUDINARY_CLOUD_NAME=your_cloud
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
GOOGLE_MAPS_API_KEY=your_maps_key
```

> `GOOGLE_MAPS_API_KEY` is exposed to templates via `buildback.context_processors.google_maps_key`.

---

## URL Routes

| Path | View | Name |
|------|------|------|
| `/` | `home` | `home` |
| `/browse/` | `browse` | `browse` |
| `/sell/` | `sell` | `sell` |
| `/listing/<pk>/` | `detail` | `detail` |
| `/my-listings/` | `my_listings` | `my_listings` |
| `/edit/<pk>/` | `edit_listing` | `edit_listing` |
| `/delete/<pk>/` | `delete_listing` | `delete_listing` |
| `/sold/<pk>/` | `mark_sold` | `mark_sold` |
| `/register/` | `register` | `register` |
| `/login/` | `user_login` | `login` |
| `/logout/` | `user_logout` | `logout` |
| `/calculator/estimate/` | `calculate_estimate` | `calculate_estimate` |

---

## Running Tests

```bash
# All tests (uses SQLite in-memory)
python manage.py test marketplace.tests -v 2

# Specific test
python manage.py test marketplace.tests.CalculatorTests.test_calculator_savings -v 2
```

**Test Coverage**: 4 tests for `estimate_savings()`:
- `test_calculator_savings` — positive savings case
- `test_calculator_not_worth_it` — negative savings
- `test_calculator_min_fare` — min fare > distance×rate
- `test_calculator_zero_distance` — same location

---

## Common Tasks

### Add a new category
1. Update `Material.CATEGORY_CHOICES` in `models.py`
2. Add SVG icon in `home.html` category grid
3. Run `makemigrations` + `migrate`

### Modify calculator logic
1. Edit `services.py::estimate_savings()`
2. Add test case in `tests.py`
3. Run tests

### Add a new page
1. Create view in `views.py`
2. Add route in `marketplace/urls.py`
3. Create template extending `base.html`
4. Add nav link in `base.html` header

### Deploy checklist
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` set
- [ ] Real `SECRET_KEY`
- [ ] Production MySQL
- [ ] Cloudinary credentials
- [ ] Google Maps API key (restrict to domain)
- [ ] Static files: `collectstatic` + CDN
- [ ] HTTPS + secure cookies
- [ ] Run migrations

---

## Gotchas & Notes

- **Google Maps**: Distance Matrix called **server-side only** (API key in `.env`, not exposed to client). Places Autocomplete + JS Map use client-side key (restrict via HTTP referrer).
- **Images**: Upload handled client-side → Cloudinary (unsigned upload preset recommended). `sell.js` stores preview URLs; replace with Cloudinary URLs on success.
- **Location permission**: If denied, user falls back to manual map pin/autocomplete.
- **CSRF**: All POST forms use `{% csrf_token %}`; AJAX endpoints use `X-CSRFToken` header (set in `base.html`).
- **Distance cache**: Rounded to 4 decimal places (~11m). Key = `(origin_lat, origin_lng, dest_lat, dest_lng)`.
- **No payments/chat/ratings** in Phase 1 — direct phone/WhatsApp contact only.

---

## Future Phases (Out of Scope)

| Phase | Features |
|-------|----------|
| 2 | Payments, escrow, chat, ratings, push notifications |
| 3 | Admin dashboard, analytics, bulk import, seller verification |
| 4 | PWA, offline support, image optimization, multi-language |

---

## License
Proprietary — BuildBack Mini Project Phase 1.