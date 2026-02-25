# Audit Action Checklist

Quick reference checklist for implementing audit fixes.

## 🔴 Priority 1: Critical (Do First)

### SubCategory References Removal
- [ ] Fix `catalog/management/commands/populate_vocational.py`
- [ ] Update `populate_categories.py`
- [ ] Update `populate_dummy_data.py`
- [ ] Fix `stress_tests/fixtures/generate_test_data.py`
- [ ] Update `templates/catalog/vocational_index.html`
- [ ] Update `templates/catalog/index.html`
- [ ] Update `templates/catalog/category_list.html`
- [ ] Update `templates/admin/catalog/testbank/upload_json.html`

### Security Fixes
- [ ] Move SECRET_KEY to .env only (remove from settings.py)
- [ ] Add rate limiting to AJAX endpoints
- [ ] Add JSON size validation in `rate_test_bank()`
- [ ] Add question-session validation in `save_answer()`
- [ ] Enable production security settings

### Code Cleanup
- [ ] Remove duplicate `JsonResponse` import in `catalog/views.py`
- [ ] Remove duplicate `json` import in `catalog/views.py`
- [ ] Remove unused `Avg` import in `catalog/views.py`
- [ ] Remove unused `Http404` import in `cms/views.py`
- [ ] Fix `models.Q` import in `cms/views.py` (import `Q` directly)

---

## 🟡 Priority 2: High (Do Soon)

### Performance Optimization
- [ ] Add `select_related` to `catalog/views.py - index()`
- [ ] Add `select_related` to `accounts/views.py - dashboard()`
- [ ] Add `select_related`/`prefetch_related` to `catalog/views.py - testbank_detail()`
- [ ] Add database index to `UserAnswer.answered_at`
- [ ] Add database index to `TestBank.certification_domain` (if needed)

### Error Handling
- [ ] Add error handling to `catalog/views.py - search()`
- [ ] Improve error handling in `payments/views.py - payment_success()`
- [ ] Add validation to `practice/views.py - save_answer()`

### Unused Code
- [ ] Remove or implement `cms/views.py - get_active_announcements()`
- [ ] Remove or implement `cms/views.py - get_content_block()`
- [ ] Document or remove unused model fields

---

## 🟢 Priority 3: Medium (Nice to Have)

### Code Refactoring
- [ ] Create slug generation utility/mixin
- [ ] Consolidate error handling in payments views
- [ ] Refactor duplicate code

### Testing
- [ ] Add tests for accounts app views
- [ ] Add tests for payments app views
- [ ] Add tests for cms app views
- [ ] Add tests for forum app views
- [ ] Add tests for catalog app models
- [ ] Add form validation tests
- [ ] Add security tests
- [ ] Add integration tests
- [ ] Set up test coverage reporting

### Documentation
- [ ] Add API documentation
- [ ] Add deployment troubleshooting guide
- [ ] Add contributing guidelines
- [ ] Create changelog

---

## 🔵 Priority 4: Low (Future)

### Architecture
- [ ] Consider Django signals for cross-app communication
- [ ] Consider REST API structure
- [ ] Separate business logic from views

### Performance Monitoring
- [ ] Set up Django Debug Toolbar
- [ ] Add query logging
- [ ] Implement performance monitoring
- [ ] Add caching

---

## Quick Commands

### Find SubCategory References
```bash
grep -r "SubCategory" --include="*.py" --include="*.html" .
```

### Find Unused Imports
```bash
# Install pylint or flake8
pip install pylint
pylint --disable=all --enable=unused-import catalog/views.py
```

### Run Tests
```bash
python manage.py test
python manage.py test --coverage
```

### Check Query Count
```bash
# Add to settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

---

## Progress Tracking

**Started:** _______________  
**Target Completion:** _______________  
**Current Phase:** _______________

**Completed Items:** ___ / 50  
**Progress:** ___%

---

*Last Updated: _______________*
