# Contributing to NADOS Dv1.0

Thank you for your interest in contributing to NADOS Dv1.0!

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker
- Provide clear reproduction steps
- Include system information (OS, Python version)
- Specify which scenario or feature is affected

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`python -m pytest`)
5. Run linting (`ruff check .`)
6. Run type checking (`mypy src/nados`)
7. Commit with clear messages
8. Push to your fork
9. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/nwr031-gif/nadosdv1.0.git
cd nadosdv1.0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
pre-commit install
```

### Code Style

- Follow PEP 8 (enforced by Ruff)
- Type hints required for public APIs
- Docstrings for all public classes and functions
- Arabic-first UI strings (English only for technical identifiers)

### Testing

- Write tests for new functionality
- Maintain >85% coverage on core modules
- Use deterministic fixtures for numerical tests
- Mark GUI tests as `@pytest.mark.gui`

### Safety Requirements

All contributions must maintain the safety boundary:
- No real weapon control interfaces
- No real-world targeting data integration
- No hardware interfaces for weapon systems
- All simulated data clearly labeled as synthetic

## Pull Request Checklist

- [ ] Tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] No safety boundary violations
- [ ] Arabic UI strings included for new features

## Questions?

Open a GitHub Discussion or issue for clarification.