# Contributing to Tennis ELO

Thank you for your interest in contributing to Tennis ELO! This guide will help you get started.

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/tennis-elo.git
cd tennis-elo
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tennis_elo --cov-report=html

# Run specific test file
pytest tests/test_prediction.py

# Run specific test function
pytest tests/test_prediction.py::TestPredictionEngine::test_predict_match
```

## 💅 Code Style

```bash
# Format code with Black
black src/ tests/

# Check formatting
black --check src/ tests/

# Run linter
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports
```

## 📝 Pull Request Guidelines

### Before Submitting

- [ ] Tests added/updated and passing
- [ ] Code formatted with Black
- [ ] Linting passes (flake8)
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Branch rebased on latest main

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
Describe tests added or modified.

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

## 🎯 What We're Looking For

### High Priority Contributions

- ✅ Bug fixes with reproduction steps
- ✅ New features with comprehensive tests
- ✅ Performance improvements with benchmarks
- ✅ Additional data sources (tournaments, players)
- ✅ Documentation improvements

### Also Welcome

- ✅ Typo fixes
- ✅ Code refactoring
- ✅ Test coverage improvements
- ✅ CI/CD enhancements
- ✅ Issue triage and discussion

## 🐛 Reporting Bugs

1. **Check existing issues** - Search to see if already reported
2. **Use bug report template** - `.github/ISSUE_TEMPLATE/bug_report.md`
3. **Include**:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Code snippet if applicable

## 💡 Feature Requests

1. **Open a discussion** before creating an issue
2. **Explain the use case** - Why is this needed?
3. **Provide examples** - How would it be used?

## 🔢 Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (1.X.0): New features (backward compatible)
- **PATCH** (1.0.X): Bug fixes

## 📚 Resources

- [Project Documentation](README.md)
- [API Reference](docs/)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)

## ❓ Questions?

- Open a [discussion](https://github.com/yourusername/tennis-elo/discussions)
- Join the community chat (if available)
- Email: your.email@example.com

---

Thank you for contributing! 🎾
