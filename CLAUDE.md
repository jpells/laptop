# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ansible-based macOS laptop automation that configures a complete development environment including packages, applications, shell configuration, and system settings.

## Commands

### Setup
```bash
./bootstrap.sh              # Install Homebrew and uv package manager
uv sync                     # Create venv and install dependencies
uv run pre-commit install   # Install pre-commit hooks
```

### Run Playbook
```bash
uv run ansible-playbook laptop.yml                    # Full run
uv run ansible-playbook laptop.yml --tags dotfiles    # Single tag
uv run ansible-playbook laptop.yml --tags vim,terminal # Multiple tags
uv run ansible-playbook laptop.yml --skip-tags dock   # Skip specific tasks
```

### Linting
```bash
uv run ansible-lint                        # Lint all roles
uv run pre-commit run --all-files          # Run all pre-commit hooks
uv run ansible-playbook laptop.yml --syntax-check # Syntax validation
uv run ansible-playbook laptop.yml --list-tasks   # List all tasks
```

## Architecture

Single role (`laptop`) with task files organized by function:

| Task File | Tag(s) | Purpose |
|-----------|--------|---------|
| homebrew.yml | homebrew | Homebrew packages and casks |
| mas.yml | mas | Mac App Store apps (install/uninstall) |
| dotfiles.yml | dotfiles | Copy config files to home directory |
| scripts.yml | scripts | Install utility scripts to ~/.local/bin |
| vim.yml | vim | Vim/Neovim plugin manager and plugins |
| vscode.yml | vscode | VS Code extension installation |
| terminal.yml | terminal | Terminal.app and iTerm2 configuration |
| dock.yml | dock | Dock app arrangement |
| macos.yml | macos | macOS system defaults |
| backup.yml | backup | Backup cron job (personal profile only) |
| restore.yml | restore | Restore from NAS backup |

### Key Paths
- **Main playbook**: `laptop.yml`
- **Role tasks**: `roles/laptop/tasks/`
- **Variables** (packages, apps, paths): `roles/laptop/vars/main.yml`
- **Dotfiles** (zshrc, vimrc, gitconfig, etc.): `roles/laptop/files/dotfiles/`
- **Utility scripts**: `roles/laptop/files/scripts/` (synology-cloudsync-decrypt)
- **Terminal profiles**: `roles/laptop/files/` (JJ.terminal, iterm2 plist)
- **Templates**: `roles/laptop/templates/` (gitconfig.j2, backup.sh.j2, restore.sh.j2)
- **Handlers**: `roles/laptop/handlers/main.yml` (Restart Dock, Restart Finder)

### Dotfiles
Dotfiles in `roles/laptop/files/dotfiles/` are copied to their home directory locations (e.g., `dotfiles/zshrc` → `~/.zshrc`). The file list is defined in `roles/laptop/tasks/dotfiles.yml`.

### Variable Naming Convention
Variables use a profile-based naming pattern:
- `laptop_base_*` - Applied to all machines
- `laptop_personal_*` - Additional items for personal (non-work) setups

Both are merged at runtime for packages, casks, mas_apps, and dock_apps.

## Bootstrap Process

The `bootstrap.sh` script handles initial system setup before Ansible can run:

1. **Installs Homebrew** (if not present)
   - Apple Silicon: `/opt/homebrew/bin/brew`
   - Intel: `/usr/local/bin/brew`
   - Sets NONINTERACTIVE=1 to prevent prompts

2. **Installs uv via Homebrew** (if not present)
   - Manages uv as a Homebrew package for easy updates
   - Ensures `brew` command is available by evaluating shellenv

3. **Outputs next steps** for user to run

The bootstrap script is idempotent and can be safely re-run. The Ansible playbook's Homebrew tasks will also ensure both tools are present, making the playbook independently runnable without bootstrap.
