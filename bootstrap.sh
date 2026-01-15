#!/bin/bash
set -euo pipefail

# Color output for better UX
echo "==> Bootstrapping laptop setup..."

# Step 1: Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    echo "==> Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Evaluate Homebrew environment for Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "==> Homebrew already installed"
    # Ensure brew is in PATH even if already installed
    if [[ $(uname -m) == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# Step 2: Install uv via Homebrew
if ! brew list uv &> /dev/null; then
    echo "==> Installing uv via Homebrew..."
    brew install uv
else
    echo "==> uv already installed via Homebrew"
fi

echo ""
echo "==> Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. uv sync                                    # Install Ansible and dependencies"
echo "  2. uv run pre-commit install                  # Install pre-commit hooks"
echo "  3. export GIT_USER_NAME='Your Name'"
echo "  4. export GIT_USER_EMAIL='you@example.com'"
echo "  5. uv run ansible-playbook laptop.yml -e laptop_profile=personal -K"
