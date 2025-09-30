#!/bin/bash

# Atlas Travel Demo - Linting Setup Script
# This script sets up pre-commit hooks and linting tools

set -e

echo "🚀 Setting up linting and pre-commit hooks for Atlas Travel Demo..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: This script must be run from the root of a git repository"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing linting dependencies..."

# Check if we're in a virtual environment or have pip available
if command -v pip &> /dev/null; then
    echo "Installing pre-commit and linting tools..."
    pip install pre-commit==3.6.0 black==23.12.1 isort==5.13.2 flake8==7.0.0 mypy==1.8.0
else
    echo "⚠️  Warning: pip not found. Please install the dependencies manually:"
    echo "   pip install pre-commit==3.6.0 black==23.12.1 isort==5.13.2 flake8==7.0.0 mypy==1.8.0"
fi

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to ensure everything is set up correctly
echo "🧹 Running initial pre-commit check..."
pre-commit run --all-files || {
    echo "⚠️  Some files were reformatted. This is normal for the first run."
    echo "   The files have been automatically fixed."
}

echo ""
echo "✅ Linting setup complete!"
echo ""
echo "📋 What happens now:"
echo "   • Every time you commit, code will be automatically linted and formatted"
echo "   • If there are issues, the commit will be blocked until they're fixed"
echo "   • Most formatting issues will be auto-fixed"
echo ""
echo "🛠️  Available commands:"
echo "   make lint              - Run linters manually"
echo "   make format            - Format code manually"
echo "   make pre-commit-run    - Run pre-commit hooks manually"
echo ""
echo "🎉 Happy coding with clean, consistent code!"
