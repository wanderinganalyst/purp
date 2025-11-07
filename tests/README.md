# Testing Documentation

## Overview

Comprehensive test suite for the Purp application covering unit tests, integration tests, end-to-end tests, and Docker container tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── unit/                          # Unit tests for individual modules
│   ├── test_validators.py         # Input validation tests
│   ├── test_data_fetcher.py       # Data fetcher tests
│   └── test_models.py             # Database model tests
├── integration/                   # Integration tests
│   ├── test_auth_routes.py        # Authentication route tests
│   └── test_bills_routes.py       # Bills route tests
├── e2e/                           # End-to-end tests
│   └── test_forms.py              # HTML form and validation tests
└── docker/                        # Docker tests
    └── test_docker.py             # Docker build and container tests
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov beautifulsoup4 requests

# Run all tests
python run_tests.py

# Or use the shell script
chmod +x run_tests.sh
./run_tests.sh
```

### Running Specific Test Suites

```bash
# Unit tests only
python run_tests.py unit

# Integration tests only
python run_tests.py integration

# End-to-end tests only
python run_tests.py e2e

# Docker tests only
python run_tests.py docker
```

### With Verbose Output

```bash
python run_tests.py all --verbose
# or
./run_tests.sh all -v
```

### With Coverage Report

```bash
python run_tests.py all --coverage
# or
./run_tests.sh all -c

# View coverage report
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual functions and classes in isolation.

**test_validators.py**
- Username validation (length, characters, format)
- Password strength validation
- Address validation
- Apartment/unit validation
- Comment content validation
- Input sanitization

**test_data_fetcher.py**
- Singleton pattern
- Environment detection (production vs development)
- Mock data generation and caching
- Bills fetching
- Representatives fetching by zip code
- Fallback for unknown zip codes

**test_models.py**
- User model creation
- Password hashing and verification
- Representative information updates
- User-comment relationships
- Unique constraints

### Integration Tests (`tests/integration/`)

Test interactions between components, routes, and database.

**test_auth_routes.py**
- Login page rendering
- Successful login
- Failed login (wrong password, nonexistent user)
- User registration
- Duplicate username prevention
- Password mismatch detection
- Logout functionality
- Profile page access
- Role-based access control

**test_bills_routes.py**
- Bills list page rendering
- Bill display
- Bill detail page
- Comment submission (authenticated users)
- Comment validation
- XSS prevention in comments

### End-to-End Tests (`tests/e2e/`)

Test complete user workflows and UI interactions.

**test_forms.py**
- Login form structure and validation
- Signup form fields and validation
- Password field security
- Comment form visibility
- Form security (POST methods, no plaintext passwords)
- XSS prevention
- SQL injection prevention
- Bootstrap responsive design
- Form labels and accessibility
- Error message display

### Docker Tests (`tests/docker/`)

Test Docker containerization and deployment.

**test_docker.py**
- Dockerfile existence and syntax
- Docker image build
- Docker image size
- docker-compose configuration
- Container startup
- HTTP response from container
- Environment configuration
- Resource cleanup

## Test Fixtures

Defined in `tests/conftest.py`:

- `app`: Test Flask application instance
- `client`: Test client for making requests
- `db_session`: Database session for test isolation
- `auth_client`: Authenticated user client
- `admin_client`: Authenticated admin client
- `sample_bill`: Sample bill data
- `sample_address`: Sample address data

## Writing New Tests

### Unit Test Example

```python
# tests/unit/test_my_module.py
import pytest
from my_module import my_function

class TestMyFunction:
    def test_valid_input(self):
        """Test with valid input."""
        result = my_function('valid')
        assert result == expected_value
    
    def test_invalid_input(self):
        """Test with invalid input."""
        with pytest.raises(ValueError):
            my_function('invalid')
```

### Integration Test Example

```python
# tests/integration/test_my_routes.py
import pytest

class TestMyRoute:
    def test_route_requires_auth(self, client):
        """Test that route requires authentication."""
        response = client.get('/my-route')
        assert response.status_code in [302, 401]
    
    def test_route_with_auth(self, auth_client):
        """Test route with authenticated user."""
        response = auth_client.get('/my-route')
        assert response.status_code == 200
```

### Form Test Example

```python
# tests/e2e/test_my_form.py
from bs4 import BeautifulSoup

class TestMyForm:
    def test_form_exists(self, client):
        """Test that form exists."""
        response = client.get('/form-page')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        form = soup.find('form')
        assert form is not None
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.slow
def test_long_running():
    pass

@pytest.mark.docker
def test_container():
    pass
```

Run specific markers:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
pytest -m docker        # Run only docker tests
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov beautifulsoup4
      - name: Run tests
        run: python run_tests.py all --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Coverage Goals

- **Unit Tests**: Aim for 80%+ coverage of utility functions and models
- **Integration Tests**: Cover all API endpoints and routes
- **E2E Tests**: Cover critical user workflows
- **Docker Tests**: Verify deployment and containerization

## Troubleshooting

### Tests Fail to Import Modules

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run tests with:
python -m pytest tests/
```

### Database Errors

Tests use a temporary SQLite database that's created and destroyed for each test session. If you see database errors:

```bash
# Clean up any test databases
rm -f tests/*.db
rm -f instance/test*.db
```

### Docker Tests Fail

```bash
# Ensure Docker is running
docker ps

# Clean up test containers
docker rm -f $(docker ps -aq --filter ancestor=purp-test)
docker rmi purp-test
```

### Port Already in Use

If tests fail because port 5000 is in use:

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or change test port in conftest.py
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names (test_what_when_then)
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Fixtures**: Use fixtures for common setup
5. **Mocking**: Mock external dependencies (API calls, file I/O)
6. **Coverage**: Aim for high coverage but focus on quality
7. **Fast Tests**: Keep unit tests fast, mark slow tests
8. **Documentation**: Document complex test scenarios

## Performance

Run tests in parallel for faster execution:

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Debugging Tests

```bash
# Run with more verbose output
pytest -vv

# Stop on first failure
pytest -x

# Run specific test
pytest tests/unit/test_validators.py::TestValidateUsername::test_valid_username

# Drop into debugger on failure
pytest --pdb

# Print output (disable capture)
pytest -s
```

## Test Data

Mock data is generated in development mode:
- Bills: 8 sample Missouri bills
- Representatives: Data for Jefferson City, St. Louis, Kansas City
- Users: Created per test with unique usernames

## Security Testing

Tests include security checks for:
- XSS prevention
- SQL injection prevention
- CSRF protection
- Password hashing
- Input sanitization
- Authentication enforcement
- Role-based access control

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
