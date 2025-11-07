# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### 1. Test Suite (`test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**
- **test**: Runs all tests across Python 3.10 and 3.11
  - Linting with flake8
  - Code formatting check with black
  - Unit tests
  - Integration tests
  - End-to-end tests
  - Coverage reporting (uploads to artifacts)

- **docker-tests**: Tests Docker builds
  - Builds Docker image
  - Tests container startup
  - Tests docker-compose setup

- **security-scan**: Security analysis
  - Dependency scanning with Safety
  - Code scanning with Bandit

- **infrastructure-validation**: Validates IaC
  - Terraform format check
  - Terraform validation for all modules
  - Ansible syntax check

- **status-check**: Final gate
  - Ensures all required jobs passed
  - Blocks merge if any critical test fails

### 2. Branch Protection (`branch-protection.yml`)

**Triggers:**
- Pull request events (opened, synchronized, reopened)

**Enforcement:**
- All tests must pass (zero failures allowed)
- Code coverage must be ≥60%
- Blocks PR merge if requirements not met

## Local Pre-Commit Hook

A pre-commit hook is installed at `.git/hooks/pre-commit` that runs:
1. Python syntax check
2. Flake8 critical errors check
3. Quick unit tests

**Skip pre-commit checks** (not recommended):
```bash
git commit --no-verify -m "your message"
```

## Setting Up Branch Protection on GitHub

After pushing to GitHub, configure branch protection rules:

### For `main` branch:

1. Go to **Settings** → **Branches** → **Add branch protection rule**
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Search and require: `test`
     - Search and require: `docker-tests`
     - Search and require: `status-check`
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings
4. Click **Create** or **Save changes**

### For `develop` branch (recommended):

Same as above, but for branch pattern: `develop`

## Required Status Checks

The following checks must pass before merging:
- ✅ `test` - All unit/integration/e2e tests
- ✅ `docker-tests` - Docker build and runtime tests
- ✅ `status-check` - Overall status verification

Optional (will run but won't block):
- 🔍 `security-scan` - Security vulnerability scanning
- 🔍 `infrastructure-validation` - Terraform/Ansible validation

## Workflow Status Badges

Add these to your main README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/purp/workflows/Test%20Suite/badge.svg)
![Security](https://github.com/YOUR_USERNAME/purp/workflows/Branch%20Protection/badge.svg)
```

## Environment Variables & Secrets

If you need to add secrets for CI/CD:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add secrets as needed (e.g., `AWS_ACCESS_KEY_ID`, `DATABASE_URL`)

## Coverage Reports

After each test run, coverage reports are uploaded as artifacts:
- HTML coverage report: `coverage-report-py3.10`
- HTML coverage report: `coverage-report-py3.11`

Download from the **Actions** tab → Select workflow run → **Artifacts**

## Testing Locally

Before pushing, ensure tests pass locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run linting
flake8 . --exclude=.venv,venv,infrastructure

# Check formatting
black --check . --exclude '/(\.venv|venv|infrastructure)/'
```

## Troubleshooting

### Tests fail in CI but pass locally
- Check Python version (CI tests 3.10 and 3.11)
- Ensure all dependencies in `requirements.txt`
- Check for environment-specific issues

### Docker tests fail
- Verify `Dockerfile` builds successfully
- Check `docker-compose.yml` syntax
- Test locally: `docker-compose up --build`

### Infrastructure validation fails
- Run `terraform fmt` in terraform directories
- Run `terraform validate` on each module
- Run `ansible-playbook --syntax-check` on playbooks

## Performance

**Typical CI run times:**
- Test job: ~3-5 minutes
- Docker tests: ~2-3 minutes
- Security scan: ~1-2 minutes
- Infrastructure validation: ~1 minute
- **Total**: ~7-11 minutes

## Caching

The workflows use caching to speed up runs:
- Pip packages cached (based on `requirements.txt` hash)
- Docker layers cached via BuildKit

## Cost

GitHub Actions is free for public repositories and includes:
- 2,000 minutes/month for private repos (free tier)
- This CI setup uses ~10-15 minutes per push
- Approximately 130-200 pushes/month on free tier

## Future Enhancements

Potential additions:
- [ ] Deploy to staging on merge to `develop`
- [ ] Deploy to production on merge to `main`
- [ ] Performance testing
- [ ] Visual regression testing
- [ ] Automated dependency updates (Dependabot)
- [ ] Code quality metrics (SonarCloud)
- [ ] Slack/Discord notifications
