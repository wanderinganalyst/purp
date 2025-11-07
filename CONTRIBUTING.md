# Contributing to Purp

Thank you for considering contributing to Purp! This document outlines the process and guidelines.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/purp.git
   cd purp
   ```
3. **Set up development environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install pytest pytest-cov flake8 black
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions/changes
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clear, concise code
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed

### 3. Test Your Changes

**Run all tests:**
```bash
pytest
```

**Run specific test categories:**
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only
```

**Check coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Lint your code:**
```bash
flake8 . --exclude=.venv,venv,infrastructure
```

**Format your code:**
```bash
black . --exclude '/(\.venv|venv|infrastructure)/'
```

### 4. Commit Your Changes

The repository has a pre-commit hook that runs tests automatically.

```bash
git add .
git commit -m "feat: Add new feature description"
```

**Commit message format:**
```
type: Short description (max 72 chars)

Longer description if needed.

Fixes #123
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Maintenance tasks

**Skip pre-commit hook** (not recommended):
```bash
git commit --no-verify -m "message"
```

### 5. Push to GitHub

```bash
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

1. Go to your fork on GitHub
2. Click **"New Pull Request"**
3. Select your branch
4. Fill out the PR template
5. Submit for review

## Code Standards

### Python Style

- Follow **PEP 8**
- Maximum line length: 127 characters
- Use **Black** for formatting
- Use type hints where appropriate

### Testing Requirements

- All new features must have tests
- Maintain test coverage ≥60%
- Tests must pass before merging
- Use descriptive test names

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update infrastructure docs for deployment changes

## Pull Request Process

### PR Checklist

Before submitting, ensure:
- [ ] Tests pass locally (`pytest`)
- [ ] Code is formatted (`black`)
- [ ] No linting errors (`flake8`)
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description is clear

### GitHub Actions CI

When you create a PR, GitHub Actions will automatically:
1. ✅ Run all tests (Python 3.10 & 3.11)
2. ✅ Check code formatting
3. ✅ Run linting
4. ✅ Build Docker containers
5. ✅ Validate infrastructure code
6. ✅ Run security scans
7. ✅ Check test coverage

**All checks must pass before merge.**

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review comments
4. Keep PR up-to-date with main branch

## Testing Guidelines

### Writing Tests

**Unit tests** (`tests/unit/`):
- Test individual functions/classes
- Mock external dependencies
- Fast execution

**Integration tests** (`tests/integration/`):
- Test multiple components together
- Test route handlers
- Test database interactions

**E2E tests** (`tests/e2e/`):
- Test complete user workflows
- Test form submissions
- Test authentication flows

### Test Structure

```python
def test_feature_name_should_do_something():
    """Test that feature does something specific."""
    # Arrange
    setup_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

### Running Specific Tests

```bash
# Run single test file
pytest tests/unit/test_validators.py

# Run single test function
pytest tests/unit/test_validators.py::test_zip_code_validation

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Stop on first failure
pytest -x
```

## Infrastructure Changes

If modifying infrastructure code:

1. **Terraform changes:**
   ```bash
   cd infrastructure/terraform
   terraform fmt
   terraform validate
   ```

2. **Ansible changes:**
   ```bash
   cd infrastructure/ansible
   ansible-playbook playbooks/deploy-app.yml --syntax-check
   ```

3. Update infrastructure documentation

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version)
- Relevant logs/screenshots

### Feature Requests

Include:
- Clear description of the feature
- Use case / problem it solves
- Proposed solution (optional)
- Alternative solutions considered

## Code Review Guidelines

### For Reviewers

- Be respectful and constructive
- Explain reasoning for changes
- Approve when all concerns addressed
- Test changes if possible

### For Contributors

- Respond to all comments
- Ask for clarification if needed
- Make requested changes
- Mark conversations as resolved

## Getting Help

- 📖 Read the [README.md](README.md)
- 🏗️ Check [infrastructure/README.md](infrastructure/README.md)
- 🧪 Review [tests/README.md](tests/README.md)
- 💬 Ask questions in PR comments
- 🐛 Search existing issues

## Local Development Tips

### Activate Virtual Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Run Development Server

```bash
python app.py
# or
flask run
```

### Watch Tests

```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
ptw
```

### Database

```bash
# Reset database
rm instance/*.db
python init_db.py
```

## Release Process

(For maintainers)

1. Update version in `__init__.py` or `setup.py`
2. Update CHANGELOG.md
3. Create release branch: `release/vX.Y.Z`
4. Merge to main
5. Tag release: `git tag vX.Y.Z`
6. Push tag: `git push --tags`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

Feel free to ask questions by:
- Opening an issue
- Commenting on relevant PRs
- Reaching out to maintainers

Thank you for contributing! 🎉
