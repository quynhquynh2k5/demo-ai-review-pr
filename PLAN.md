# PR Agent Test Project - Plan

## Mục tiêu

Xây dựng một e-commerce API (FastAPI + PostgreSQL) với các kịch bản lỗi có chủ đích để đánh giá khả năng review code của PR Agent (AI reviewer).

## Pipeline context

```
Code Push → Black → flake8 → mypy → SonarQube → AI Review
```

AI reviewer chỉ cần tập trung vào các lỗi mà **static analysis tools không bắt được**: logic errors, security vulnerabilities, concurrency issues, business logic flaws, etc.

---

## Tổng quan kịch bản test

| PR | Scenario | Bugs | Kích thước | Test điều gì | Trạng thái |
|----|----------|------|------------|--------------|------------|
| #1 | Phase 2a: Easy bugs | 5 | Small ~100 lines | Baseline - AI bắt lỗi hiển nhiên? | ⬜ Chưa làm |
| #2 | Phase 2b: Hard bugs | 5 | Medium ~200 lines | AI bắt lỗi subtle? | ⬜ Chưa làm |
| #3 | Phase 2c: Clean PR | 0 | Medium ~150 lines | False positive rate | ⬜ Chưa làm |
| #4 | Phase 2d: Misleading PR description | 5 | Small ~100 lines | AI bị bias bởi title/description? | ⬜ Chưa làm |
| #5 | Phase 3a: Large PR mixed | ~35 | Large ~500+ lines | AI xử lý PR lớn? | ⬜ Chưa làm |
| #6 | Phase 3b: Refactor noise | ~35 | Large ~600+ lines | AI bị distract bởi noise? | ⬜ Chưa làm |

**Tổng: 6 PRs, ~85 bugs cài đặt**

---

## Phase 1: Base Project (Clean, working e-commerce API) ✅ DONE

### Tech stack

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Auth**: JWT
- **Validation**: Pydantic v2

### Domain models

```
User        → id, email, password_hash, is_admin, balance, created_at
Product     → id, name, description, price (Decimal), stock, category, created_at
Order       → id, user_id, status, total_amount, discount_amount, tax_amount, created_at
OrderItem   → id, order_id, product_id, quantity, unit_price
Cart        → id, user_id
CartItem    → id, cart_id, product_id, quantity
Coupon      → id, code, discount_percent, max_uses, current_uses, is_active, expires_at
Review      → id, user_id, product_id, rating, comment, created_at
```

### API endpoints

```
Auth:
  POST   /auth/register
  POST   /auth/login
  GET    /auth/me

Products:
  GET    /products              (list, search, filter, paginate)
  GET    /products/{id}
  POST   /products              (admin)
  PUT    /products/{id}         (admin)
  DELETE /products/{id}         (admin)

Cart:
  GET    /cart
  POST   /cart/items
  PUT    /cart/items/{id}
  DELETE /cart/items/{id}

Orders:
  POST   /orders/checkout
  GET    /orders
  GET    /orders/{id}
  PUT    /orders/{id}/cancel

Coupons:
  POST   /coupons               (admin)
  POST   /coupons/apply

Reviews:
  POST   /products/{id}/reviews
  GET    /products/{id}/reviews

Users (admin):
  GET    /admin/users
  PUT    /admin/users/{id}
  DELETE /admin/users/{id}
```

### Project structure

```
src/
├── main.py
├── config.py
├── database.py
├── models/
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   ├── cart.py
│   ├── coupon.py
│   └── review.py
├── schemas/
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   ├── cart.py
│   ├── coupon.py
│   └── review.py
├── api/
│   ├── auth.py
│   ├── products.py
│   ├── cart.py
│   ├── orders.py
│   ├── coupons.py
│   ├── reviews.py
│   └── admin.py
├── services/
│   ├── auth.py
│   ├── product.py
│   ├── order.py
│   ├── cart.py
│   ├── coupon.py
│   └── review.py
├── dependencies.py
└── utils/
    ├── security.py
    └── pagination.py
tests/
├── conftest.py
├── test_auth.py
├── test_products.py
├── test_cart.py
├── test_orders.py
└── test_coupons.py
scenarios/
├── phase2a_easy_bugs/
│   └── answer_key.yaml
├── phase2b_hard_bugs/
│   └── answer_key.yaml
├── phase2c_clean_pr/
│   └── answer_key.yaml
├── phase2d_misleading_pr/
│   └── answer_key.yaml
├── phase3a_many_bugs/
│   └── answer_key.yaml
└── phase3b_refactor_bugs/
    └── answer_key.yaml
```

---

## Phase 2a: 5 lỗi dễ thấy (obvious bugs) — PR #1 ⬜ Chưa làm

> **PR**: branch `feature/product-search-v2` → `main`
> **Mô tả PR**: "Improve product search and add admin utils"
> **Kích thước**: Small PR (~100 lines, 2-3 files)

| # | File | Bug | Category | Severity | CWE |
|---|------|-----|----------|----------|-----|
| 1 | `api/products.py` | SQL injection trong search endpoint - dùng f-string thay parameterized query | Security | Critical | CWE-89 |
| 2 | `config.py` | Hardcoded DB password trong source code | Security | Critical | CWE-798 |
| 3 | `api/admin.py` | DELETE `/admin/users/{id}` thiếu auth decorator - ai cũng xóa được user | Security | Critical | CWE-862 |
| 4 | `api/cart.py` | Không validate negative quantity → user thêm quantity=-5 tạo "refund" ảo | Logic | High | CWE-20 |
| 5 | `services/order.py` | `except Exception: pass` nuốt payment error → order status sai | Error Handling | High | CWE-390 |

---

## Phase 2b: 5 lỗi khó thấy (subtle bugs) — PR #2 ⬜ Chưa làm

> **PR**: branch `feature/checkout-improvements` → `main`
> **Mô tả PR**: "Optimize checkout flow and fix edge cases"
> **Kích thước**: Medium PR (~200 lines, 4-5 files)

| # | File | Bug | Category | Severity | CWE |
|---|------|-----|----------|----------|-----|
| 1 | `services/order.py` | Race condition: check stock → deduct stock không atomic, 2 users mua cùng item cuối | Concurrency | Critical | CWE-362 |
| 2 | `services/order.py` | Dùng `float` tính tiền thay `Decimal` → sai 0.01$ khi tổng lớn | Data Integrity | Medium | CWE-681 |
| 3 | `services/order.py` | TOCTOU: validate inventory rồi mới place order, giữa 2 bước stock có thể thay đổi | Concurrency | High | CWE-367 |
| 4 | `api/orders.py` | IDOR: `GET /orders/{id}` không check `order.user_id == current_user.id` → user A xem order user B | Security | High | CWE-639 |
| 5 | `services/coupon.py` | Discount apply trước tax: `(price - discount) * tax` thay vì `price * tax - discount` → tính sai tax | Logic | Medium | CWE-682 |

---

## Phase 2c: Clean PR - test false positive — PR #3 ⬜ Chưa làm

> **PR**: branch `feature/review-system` → `main`
> **Mô tả PR**: "Add product review and rating system"
> **Kích thước**: Medium PR (~150 lines, 3-4 files)
> **Bug count: 0**

Code hoàn toàn đúng, best practices. Mục tiêu: đo **false positive rate** của AI reviewer.

Đánh giá:
- AI không nên báo bug nào → PASS
- AI báo bug không tồn tại → FALSE POSITIVE (ghi nhận từng cái)
- AI có suggestions hợp lý (improve, not bugs) → OK, nhưng phân loại riêng

---

## Phase 2d: Misleading PR description — PR #4 ⬜ Chưa làm

> **PR**: branch `feature/search-performance` → `main`
> **Mô tả PR**: "Optimize search performance with caching and query improvements"
> **Kích thước**: Small PR (~100 lines, 3-4 files)
> **Thực tế**: PR chứa bugs không liên quan gì tới "performance optimization"

Mục tiêu: test xem AI có **bị bias bởi PR title/description** không. PR mô tả là "performance optimization" nhưng thực tế chứa security và logic bugs.

| # | File | Bug | Category | Severity | Difficulty | CWE |
|---|------|-----|----------|----------|------------|-----|
| 1 | `api/products.py` | SSRF: search endpoint nhận external URL để fetch product data | Security | High | Medium | CWE-918 |
| 2 | `services/cache.py` | `pickle.loads()` từ untrusted cache data | Security | High | Hard | CWE-502 |
| 3 | `config.py` | JWT token không có expiration time | Security Config | High | Medium | CWE-613 |
| 4 | `services/product.py` | Misleading variable: `is_available` thực ra check `is_deleted` logic ngược | Logic | Medium | Hard | - |
| 5 | `api/products.py` | CORS wildcard `allow_origins=["*"]` trong middleware config | Security Config | Medium | Medium | CWE-942 |

Đánh giá bổ sung:
- AI có bị ảnh hưởng bởi PR description và chỉ focus vào "performance"? → BIAS
- AI vẫn phát hiện bugs không liên quan tới description? → GOOD

---

## Phase 3a: ~35 lỗi mixed difficulty (large PR) — PR #5 ⬜ Chưa làm

> **PR**: branch `feature/full-ecommerce-v2` → `main`
> **Mô tả PR**: "Major update: checkout, payments, admin panel, caching"
> **Kích thước**: Large PR (~500+ lines, 10+ files)

### Security (10 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 1 | `api/products.py` | SQL injection trong product search | Critical | Easy | CWE-89 |
| 2 | `config.py` | Hardcoded JWT secret: `secret_key = "supersecret123"` | Critical | Easy | CWE-798 |
| 3 | `api/admin.py` | Path traversal trong upload avatar: `open(f"uploads/{filename}")` | Critical | Medium | CWE-22 |
| 4 | `services/webhook.py` | SSRF: user-controlled URL trong `requests.get(webhook_url)` | High | Medium | CWE-918 |
| 5 | `services/cache.py` | `pickle.loads()` từ Redis cache mà không verify | High | Hard | CWE-502 |
| 6 | `api/auth.py` | Login endpoint không rate limit → brute force | Medium | Medium | CWE-307 |
| 7 | `services/order.py` | Log chứa `card_number` trong payment response | High | Medium | CWE-532 |
| 8 | `api/auth.py` | Mass assignment: user register có thể set `is_admin=True` qua request body | Critical | Easy | CWE-915 |
| 9 | `config.py` | JWT token không set expiration → token sống mãi | High | Medium | CWE-613 |
| 10 | `main.py` | CORS wildcard `allow_origins=["*"]` cho phép mọi domain | Medium | Medium | CWE-942 |

### Logic (9 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 11 | `api/products.py` | Off-by-one trong pagination: skip first item | Low | Medium | CWE-193 |
| 12 | `services/coupon.py` | Discount > 100% không bị chặn → negative price | High | Easy | CWE-20 |
| 13 | `api/cart.py` | Negative quantity tạo credit ảo | High | Easy | CWE-20 |
| 14 | `services/order.py` | Charge payment trước khi validate inventory | High | Medium | CWE-696 |
| 15 | `services/coupon.py` | Coupon `current_uses` không increment → dùng vô hạn | High | Medium | CWE-682 |
| 16 | `api/products.py` | Sort order ngược: `order_by(Product.created_at.asc())` thay vì `.desc()` | Low | Easy | - |
| 17 | `services/order.py` | `datetime.now()` thay vì `datetime.utcnow()` → sai timezone | Medium | Medium | - |
| 18 | `services/coupon.py` | Discount stacking: apply nhiều coupon cùng lúc không bị chặn | High | Medium | CWE-837 |
| 19 | `services/order.py` | Refund abuse: cancel order nhưng coupon không được hoàn lại `current_uses` → dùng coupon vô hạn qua cancel loop | High | Hard | - |

### Concurrency (5 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 20 | `services/order.py` | Race condition: inventory deduction không lock | Critical | Hard | CWE-362 |
| 21 | `services/payment.py` | Double-submit payment: không có idempotency key | Critical | Hard | CWE-362 |
| 22 | `services/wallet.py` | Non-atomic read-modify-write trên user balance | Critical | Hard | CWE-362 |
| 23 | `services/cache.py` | Cache stampede: invalidate → nhiều requests cùng rebuild | Medium | Hard | CWE-362 |
| 24 | `services/cart.py` | Concurrent cart update: 2 requests cùng add → mất 1 item | Medium | Hard | CWE-362 |

### Error Handling (4 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 25 | `services/payment.py` | `except Exception: pass` nuốt payment gateway callback error | Critical | Easy | CWE-390 |
| 26 | `services/order.py` | External payment API fail nhưng không rollback DB transaction | High | Medium | CWE-460 |
| 27 | `services/payment.py` | Không set timeout cho `requests.post()` tới payment gateway | Medium | Medium | - |
| 28 | `services/order.py` | Retry without backoff → tự DDoS payment service | Medium | Medium | - |

### Data Integrity (4 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 29 | `models/order.py` | Dùng `Float` cho tiền thay vì `Numeric(10,2)` | Medium | Medium | CWE-681 |
| 30 | `services/product.py` | Mutable default argument: `def create(self, tags=[])` | Medium | Medium | - |
| 31 | `schemas/product.py` | Product name max 256 chars trong Pydantic nhưng DB column varchar(100) → truncation | Medium | Hard | CWE-135 |
| 32 | `services/product.py` | Misleading variable: `is_available` check ngược logic (True khi hết hàng) | Medium | Hard | - |

### Performance (3 lỗi)

| # | File | Bug | Severity | Difficulty | CWE |
|---|------|-----|----------|------------|-----|
| 33 | `services/order.py` | N+1 query: load orders rồi loop `await get_items(order.id)` | Medium | Medium | - |
| 34 | `api/products.py` | `SELECT * FROM products` không paginate, load tất cả vào RAM | Medium | Easy | - |
| 35 | `services/product.py` | `re.compile()` trong loop mỗi lần search filter | Low | Medium | - |

### Tổng Phase 3a: 35 bugs

| Category | Count | Easy | Medium | Hard |
|----------|-------|------|--------|------|
| Security | 10 | 3 | 5 | 2 |
| Logic | 9 | 2 | 5 | 2 |
| Concurrency | 5 | 0 | 0 | 5 |
| Error Handling | 4 | 1 | 3 | 0 |
| Data Integrity | 4 | 0 | 2 | 2 |
| Performance | 3 | 1 | 2 | 0 |
| **Tổng** | **35** | **7** | **17** | **11** |

---

## Phase 3b: ~35 lỗi ẩn trong refactoring PR — PR #6 ⬜ Chưa làm

> **PR**: branch `refactor/service-layer-cleanup` → `main`
> **Mô tả PR**: "Refactor: extract service layer, rename modules, improve structure"
> **Kích thước**: Large PR (~600+ lines, 15+ files)

Cùng 35 lỗi như Phase 3a nhưng **ẩn trong một PR refactoring lớn**:
- Rename files và functions (noise)
- Move code giữa các files
- Thay đổi import structure
- Bugs được cài vào giữa các thay đổi refactoring hợp lệ

Mục tiêu: test xem AI có bị **distract bởi noise** và miss bugs không.

---

## Kịch bản Cross-file Bugs (nằm trong Phase 3a/3b)

Các lỗi chỉ phát hiện được khi đọc **2+ files cùng lúc**:

| # | Files liên quan | Bug | Difficulty |
|---|----------------|-----|------------|
| 1 | `schemas/product.py` + `models/product.py` | Pydantic max_length=256 nhưng DB varchar(100) | Hard |
| 2 | `api/orders.py` + `services/order.py` | API trả `200 OK` nhưng service silently fail payment | Hard |
| 3 | `services/coupon.py` + `services/order.py` | Coupon validate ở service A, apply ở service B nhưng không re-validate → race | Hard |
| 4 | `models/order.py` + `services/order.py` | Model dùng `Decimal`, service dùng `float` → precision loss | Medium |
| 5 | `api/auth.py` + `schemas/user.py` | Schema cho phép field `is_admin`, API không filter → mass assignment | Medium |

---

## Scoring & Evaluation

### Metrics cho mỗi kịch bản

```yaml
# Detection metrics
detection_rate: bugs_found / total_bugs           # Mục tiêu: > 70%
false_positive_rate: false_flags / total_flags     # Mục tiêu: < 20%
severity_accuracy: correct_severity / bugs_found   # AI rate severity đúng?

# Quality metrics
review_usefulness:                                  # Đánh giá chất lượng comment
  score: 1-5                                        # 1=useless, 2=vague, 3=correct but generic,
                                                    # 4=helpful, 5=precise + fix suggestion
  explanation_quality: poor | generic | detailed    # AI giải thích bug rõ không?
  fix_suggestion: none | vague | actionable         # AI đề xuất fix cụ thể không?

# Breakdown metrics
category_breakdown:                                 # AI mạnh/yếu category nào?
  security: x/y
  logic: x/y
  concurrency: x/y
  error_handling: x/y
  data_integrity: x/y
  performance: x/y
difficulty_breakdown:                               # AI bắt được lỗi khó không?
  easy: x/y
  medium: x/y
  hard: x/y
cross_file_detection: x/y                          # AI có nhìn cross-file?

# Bias & noise metrics (Phase 2c, 2d, 3b specific)
false_positive_count: x                            # Phase 2c: bao nhiêu false flags?
description_bias: true/false                       # Phase 2d: AI có bị bias?
noise_impact: detection_3a - detection_3b          # Phase 3b: noise giảm bao nhiêu % detection?
```

### Answer key format (mỗi scenario)

```yaml
scenario: phase2a_easy_bugs
total_bugs: 5
pr_branch: feature/product-search-v2
pr_title: "Improve product search and add admin utils"
pr_description: "Add full-text search for products and utility endpoints for admin operations"
bugs:
  - id: BUG-001
    file: src/api/products.py
    line: 42-45
    category: security
    severity: critical
    difficulty: easy
    cwe: CWE-89
    title: "SQL injection in product search"
    description: "Raw f-string used in SQL query for product search endpoint"
    vulnerable_code: |
      query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
    fixed_code: |
      query = select(Product).where(Product.name.ilike(f"%{search_term}%"))
    detection_hint: "Look for string interpolation in database queries"
    cross_file: false
```

---

## Thứ tự triển khai

1. ✅ **Phase 1**: Code base project hoàn chỉnh, clean, có tests pass
2. ⬜ **Phase 2a**: Tạo branch, cài 5 easy bugs, tạo answer key → **PR #1**
3. ⬜ **Phase 2b**: Tạo branch, cài 5 hard bugs, tạo answer key → **PR #2**
4. ⬜ **Phase 2c**: Tạo branch, thêm clean feature, tạo answer key (0 bugs) → **PR #3**
5. ⬜ **Phase 2d**: Tạo branch, cài 5 bugs + misleading description, tạo answer key → **PR #4**
6. ⬜ **Phase 3a**: Tạo branch, cài 35 mixed bugs, tạo answer key → **PR #5**
7. ⬜ **Phase 3b**: Tạo branch, refactor + cài 35 bugs ẩn trong noise, tạo answer key → **PR #6**
8. ⬜ **Evaluation**: Chạy AI reviewer trên mỗi PR, so sánh với answer key, tính metrics

### Evaluation workflow

```
Với mỗi PR (#1 → #6):
  1. Tạo PR trên GitLab/GitHub
  2. Pipeline chạy: Black → flake8 → mypy → SonarQube → AI Review
  3. Thu thập AI review comments
  4. So sánh với answer_key.yaml
  5. Tính metrics (detection, false positive, usefulness)
  6. Ghi kết quả vào evaluation report

So sánh cross-scenario:
  - Phase 2a vs 2b: AI performance theo difficulty
  - Phase 2c: False positive baseline
  - Phase 2d vs 2a: Impact of misleading description
  - Phase 3a vs 2a/2b: Impact of PR size
  - Phase 3a vs 3b: Impact of refactoring noise
```
