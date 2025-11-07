#!/bin/bash
# Quick test runner script

set -e

echo "🧪 Purp Test Suite"
echo "=============================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating .venv..."
    source .venv/bin/activate || {
        echo "❌ Could not activate virtual environment"
        echo "Run: python -m venv .venv && source .venv/bin/activate"
        exit 1
    }
fi

# Install pytest if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest..."
    pip install pytest pytest-cov beautifulsoup4 requests
fi

# Parse arguments
TEST_TYPE="${1:-all}"
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        *)
            TEST_TYPE="$1"
            shift
            ;;
    esac
done

# Run tests
echo "🏃 Running ${TEST_TYPE} tests..."
echo ""

case $TEST_TYPE in
    unit)
        python -m pytest tests/unit $VERBOSE $COVERAGE
        ;;
    integration)
        python -m pytest tests/integration $VERBOSE $COVERAGE
        ;;
    e2e)
        python -m pytest tests/e2e $VERBOSE $COVERAGE
        ;;
    docker)
        python -m pytest tests/docker $VERBOSE $COVERAGE
        ;;
    all)
        python -m pytest tests $VERBOSE $COVERAGE
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Usage: $0 [unit|integration|e2e|docker|all] [-v|--verbose] [-c|--coverage]"
        exit 1
        ;;
esac

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed with exit code $EXIT_CODE"
fi

if [ -n "$COVERAGE" ]; then
    echo "📊 Coverage report: htmlcov/index.html"
fi

exit $EXIT_CODE
