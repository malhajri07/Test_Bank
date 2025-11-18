# Stress Testing Guide

This guide explains how to run load tests, performance benchmarks, and database stress tests for the Exam Stellar Django application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running Load Tests](#running-load-tests)
4. [Running Performance Benchmarks](#running-performance-benchmarks)
5. [Database Stress Tests](#database-stress-tests)
6. [Generating Test Data](#generating-test-data)
7. [Interpreting Results](#interpreting-results)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.9+
- Django development server running
- PostgreSQL database
- Test data in the database

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `locust>=2.0.0` - Load testing framework
- `pytest-benchmark>=4.0.0` - Performance benchmarking
- `httpx>=0.25.0` - HTTP client
- `faker>=20.0.0` - Test data generation

## Running Load Tests

### Using Management Command

The easiest way to run load tests is using the Django management command:

```bash
# Normal traffic scenario (50 users, 2 spawn/second, 10 minutes)
python manage.py run_load_test --scenario=normal --users=50 --spawn-rate=2 --duration=10m

# Practice exam peak scenario (100 users, 5 spawn/second)
python manage.py run_load_test --scenario=practice --users=100 --spawn-rate=5 --duration=15m

# Payment processing peak scenario
python manage.py run_load_test --scenario=payment --users=50 --spawn-rate=2 --duration=5m

# Mixed traffic scenario
python manage.py run_load_test --scenario=mixed --users=100 --spawn-rate=5 --duration=10m

# Spike test (sudden increase in load)
python manage.py run_load_test --scenario=spike --users=200 --spawn-rate=10 --duration=5m
```

### Using Locust Directly

You can also run Locust directly:

```bash
# Interactive mode (opens web UI at http://localhost:8089)
locust -f stress_tests/locustfile.py --host=http://localhost:8000

# Headless mode with HTML report
locust -f stress_tests/locustfile.py --host=http://localhost:8000 \
    --users=100 --spawn-rate=5 --run-time=10m --headless \
    --html=stress_tests/reports/locust_report.html
```

### Load Test Scenarios

#### 1. Normal Traffic
- **Users**: 50 concurrent
- **Mix**: 60% browsing, 30% practice, 10% payment
- **Duration**: 10 minutes
- **Expected**: <200ms response time, <1% error rate

#### 2. Practice Exam Peak
- **Users**: 100 concurrent
- **Behavior**: High-frequency answer saving (every 5 seconds)
- **Duration**: 15 minutes
- **Expected**: <500ms response time, <0.5% error rate

#### 3. Payment Processing Peak
- **Users**: 50 concurrent checkout sessions
- **Duration**: 5 minutes
- **Expected**: <1000ms response time, 0% error rate

#### 4. Database Stress
- **Users**: 200 concurrent
- **Queries**: Complex queries with joins
- **Duration**: 10 minutes
- **Expected**: Database connection pool handles load

#### 5. Spike Test
- **Pattern**: Sudden spike from 10 to 200 users
- **Duration**: 5 minutes
- **Expected**: Graceful degradation, no crashes

## Running Performance Benchmarks

### Using Management Command

```bash
# Run all benchmarks
python manage.py run_benchmarks

# Run benchmarks and save results
python manage.py run_benchmarks --save=baseline

# Compare against previous run
python manage.py run_benchmarks --compare

# Verbose output
python manage.py run_benchmarks --verbose
```

### Using pytest-benchmark Directly

```bash
# Run all benchmarks
pytest stress_tests/benchmarks/ --benchmark-only

# Run specific benchmark file
pytest stress_tests/benchmarks/test_views.py --benchmark-only

# Compare against previous run
pytest stress_tests/benchmarks/ --benchmark-compare

# Save results with custom name
pytest stress_tests/benchmarks/ --benchmark-save=baseline
```

### Benchmark Types

1. **View Performance** (`test_views.py`)
   - Measures response times for each view
   - Tests with different data sizes
   - Benchmarks query counts per request

2. **Database Query Performance** (`test_queries.py`)
   - Benchmarks complex queries
   - Tests N+1 query problems
   - Measures query execution time

3. **Model Operation Performance** (`test_models.py`)
   - Benchmarks bulk operations
   - Tests session creation and answer saving
   - Measures score calculation performance

## Database Stress Tests

Run database stress tests:

```bash
# Large dataset tests
pytest stress_tests/database_stress/test_large_datasets.py -v

# Concurrent query tests
pytest stress_tests/database_stress/test_concurrent_queries.py -v

# All database stress tests
pytest stress_tests/database_stress/ -v
```

## Generating Test Data

Before running stress tests, generate test data:

```bash
# Using Django shell
python manage.py shell < stress_tests/fixtures/generate_test_data.py

# OR interactively
python manage.py shell
>>> exec(open('stress_tests/fixtures/generate_test_data.py').read())
```

This will create:
- 20 categories
- 200 test banks (10 per category)
- 4000 questions (20 per test bank)
- 50 test users
- Access records and practice sessions

## Interpreting Results

### Load Test Results

After running load tests, view results:

1. **Interactive Mode**: Open http://localhost:8089 during test
2. **HTML Report**: Generated at `stress_tests/reports/locust_report.html`
3. **CSV Stats**: Generated at `stress_tests/reports/locust_stats.csv`

Generate a formatted report:

```bash
python stress_tests/reports/generate_report.py
```

### Key Metrics

- **Response Time**: Should be <500ms for most endpoints
- **Error Rate**: Should be <1% for normal traffic
- **Requests Per Second (RPS)**: Measures throughput
- **Failure Rate**: Percentage of failed requests

### Performance Benchmarks

Benchmark results are stored in `stress_tests/reports/benchmarks/`.

Compare performance over time:

```bash
python stress_tests/reports/trend_analysis.py
```

This generates a trend report at `stress_tests/reports/trend_report.html`.

### Identifying Bottlenecks

The report generator automatically identifies:
- Slow endpoints (>1000ms average response time)
- High failure rates (>1%)
- Low throughput (<1 RPS)

## Troubleshooting

### Locust Not Found

```bash
pip install locust
```

### pytest-benchmark Not Found

```bash
pip install pytest-benchmark
```

### Database Connection Errors

Ensure PostgreSQL is running and database credentials are correct in `.env`.

### Test Data Not Found

Generate test data before running tests:

```bash
python manage.py shell < stress_tests/fixtures/generate_test_data.py
```

### High Memory Usage

- Reduce number of concurrent users
- Reduce test duration
- Check for memory leaks in application code

### Slow Response Times

- Check database query optimization
- Enable database query logging: `DEBUG=True` in settings
- Review N+1 query problems
- Check database indexes

### High Error Rates

- Check application logs
- Verify test data exists
- Check CSRF token handling in load tests
- Verify user authentication in test scenarios

## Best Practices

1. **Start Small**: Begin with light load (10 users) and gradually increase
2. **Monitor Resources**: Watch CPU, memory, and database connections
3. **Run During Off-Peak**: Avoid impacting production users
4. **Baseline First**: Establish baseline metrics before optimization
5. **Regular Testing**: Run stress tests after major changes
6. **Document Results**: Keep records of test results for comparison

## Configuration Files

- **Locust Config**: `locust.conf`
- **Pytest Config**: `pytest.ini`
- **Benchmark Storage**: `stress_tests/reports/benchmarks/`

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Django Performance Best Practices](https://docs.djangoproject.com/en/stable/topics/performance/)

