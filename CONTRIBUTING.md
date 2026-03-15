# Contributing to AutoResearch

Thank you for your interest in contributing to AutoResearch! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check existing issues first
2. Use the issue templates if available
3. Provide clear details:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

### Adding New Research Types

To add a new research type:

1. Create a new function `create_<type>_research()` in `setup.py`
2. Follow the existing pattern:
   - Create configuration file
   - Create evaluation script
   - Create or copy evaluation cases
   - Generate `program.md`
   - Generate `README.md`
3. Add the type to the CLI choices in `main()`
4. Add documentation to README.md
5. Create an example in `examples/`

### Testing

Before submitting:

```bash
# Test creating each research type
python setup.py prompt /tmp/test-prompt --task "Test" --eval-cases ./examples/sentiment-classification/eval_cases.json
python setup.py ml /tmp/test-ml --task "Test"
python setup.py rag /tmp/test-rag --task "Test"
python setup.py tools /tmp/test-tools --task "Test"

# Test the example
cd examples/sentiment-classification
python eval.py  # May require API keys
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/autoresearch.git
cd autoresearch

# Install development dependencies
pip install -r requirements-dev.txt  # If available
pip install anthropic pyyaml  # For testing

# Run setup script
python setup.py --help
```

## Project Structure

```
autoresearch/
├── setup.py           # Main setup script
├── program.md         # Template for research instructions
├── README.md          # Main documentation
├── LICENSE            # MIT License
├── CONTRIBUTING.md    # This file
├── pyproject.toml     # Package configuration
└── examples/          # Example research projects
    └── sentiment-classification/
```

## Questions?

Feel free to open an issue for questions or discussions.

---

**Happy researching! 🚀**
