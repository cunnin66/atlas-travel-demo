# Code Quality & Linting Setup

This project uses automated code linting and formatting to ensure consistent, high-quality code across the entire codebase.

## 🚀 Quick Setup

Run the setup script to install and configure everything:

```bash
./setup-linting.sh
```

Or manually install using Make:

```bash
make pre-commit-install
```

## 🛠️ Tools Used

### Code Formatters
- **Black**: Opinionated Python code formatter
- **isort**: Import statement organizer

### Linters
- **flake8**: Style guide enforcement and error detection
- **mypy**: Static type checking

### Pre-commit Framework
- **pre-commit**: Manages and runs hooks before each commit

## 📋 Available Commands

### Manual Linting & Formatting
```bash
# Run all linters
make lint

# Format all code
make format

# Run pre-commit hooks manually
make pre-commit-run
```

### Pre-commit Management
```bash
# Install pre-commit hooks (one-time setup)
make pre-commit-install

# Update pre-commit hooks to latest versions
pre-commit autoupdate

# Skip pre-commit hooks for a single commit (not recommended)
git commit --no-verify -m "commit message"
```

## ⚙️ Configuration

### Tool Configuration
All tools are configured in `pyproject.toml`:
- Line length: 88 characters (Black standard)
- Import sorting: Black-compatible profile
- Type checking: Relaxed settings for gradual adoption

### Pre-commit Configuration
The `.pre-commit-config.yaml` file defines:
- Which tools run on each commit
- Tool versions and arguments
- File patterns to include/exclude

## 🔄 Workflow

### Automatic (Recommended)
1. Make your code changes
2. Run `git add` to stage files
3. Run `git commit` - hooks run automatically
4. If issues are found:
   - Most formatting issues are auto-fixed
   - Review and stage the auto-fixes: `git add .`
   - Commit again: `git commit`

### Manual
```bash
# Format code before committing
make format

# Check for issues
make lint

# Commit when everything passes
git commit -m "your message"
```

## 🚨 Common Issues & Solutions

### Import Errors
If you see import-related errors:
```bash
# Fix import organization
isort backend/ frontend/
```

### Line Length Issues
Black automatically fixes most line length issues. For complex cases:
- Break long lines manually
- Use parentheses for long expressions
- Consider refactoring complex statements

### Type Checking Errors
MyPy errors can often be resolved by:
- Adding type hints: `def function(param: str) -> int:`
- Using `# type: ignore` for third-party library issues
- Adding `from typing import` imports

### Skipping Hooks (Emergency Only)
```bash
# Skip all pre-commit hooks (not recommended)
git commit --no-verify -m "emergency fix"

# Skip specific hooks
SKIP=mypy git commit -m "skip mypy only"
```

## 📊 Benefits

- **Consistency**: All code follows the same style
- **Quality**: Catch errors before they reach production
- **Efficiency**: Automated formatting saves time
- **Collaboration**: Reduces style-related code review comments
- **Maintainability**: Cleaner, more readable code

## 🔧 Customization

To modify linting rules:

1. Edit `pyproject.toml` for tool-specific settings
2. Edit `.pre-commit-config.yaml` for hook configuration
3. Run `pre-commit install` to apply changes

## 📚 Further Reading

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)
