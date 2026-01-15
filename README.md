# Laptop

Ansible playbook for automating macOS laptop setup. Configures a complete development environment including Homebrew packages, applications, shell configuration, and system settings.

## What It Does

- **Installs packages** via Homebrew (starship, zoxide, ripgrep, bat, eza, etc.)
- **Installs applications** via Homebrew Cask (iTerm2, VS Code, Rectangle, etc.)
- **Manages Mac App Store apps** (install and uninstall)
- **Copies dotfiles** (zshrc, vimrc, gitconfig, ssh config, etc.)
- **Installs utility scripts** to ~/.local/bin
- **Configures Vim/Neovim** with plugin manager and plugins
- **Installs VS Code extensions** via code CLI
- **Sets up terminal** profiles for Terminal.app and iTerm2
- **Arranges the Dock** with preferred apps
- **Applies macOS defaults** for system preferences
- **Configures automated backup** to NAS via rsync (personal profile)

## Prerequisites

- macOS
- Command Line Tools: `xcode-select --install`

**Note:** The bootstrap script will install Homebrew and uv automatically. You don't need to install these manually.

## Quick Start

```bash
# Install Homebrew and uv package manager
./bootstrap.sh

# Install Ansible and dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Set git identity (used by gitconfig template)
export GIT_USER_NAME="Your Name"
export GIT_USER_EMAIL="you@example.com"

# Run the full playbook (-K prompts for sudo password)
uv run ansible-playbook laptop.yml -e laptop_profile=personal -K
```

## Manual Setup Steps

Some items require manual configuration after running the playbook:

### Gmail Web App (personal profile)
1. Open Safari → https://mail.google.com
2. File → Add to Dock
3. Re-run: `uv run ansible-playbook laptop.yml --tags dock`

### VS Code Settings Sync

Base VS Code extensions are installed via Ansible (see `laptop_vscode_extensions` in [vars/main.yml](roles/laptop/vars/main.yml)). Additional extensions and user settings can be managed via [Settings Sync](https://code.visualstudio.com/docs/editor/settings-sync) for personal preferences.

**Optional: Enable Settings Sync for additional extensions and settings**:
1. Open VS Code
2. Click the gear icon (⚙️) → Turn on Settings Sync
3. Sign in with GitHub or Microsoft account
4. Select what to sync (Settings, Extensions, Keyboard Shortcuts, etc.)
5. Your extensions and preferences will sync automatically across machines

### Time Machine (personal profile)

Time Machine provides full system backups and complements the automated rsync backup (which handles specific files/folders).

**Setup:**
1. Open System Settings → General → Time Machine
2. Click "Add Backup Disk" and select external drive or network volume
3. Enable Time Machine

**Recommended exclusions** (click Options in Time Machine settings):
- `~/backup` - Already backed up via automated rsync
- `~/Library/Caches` - Optional, saves space
- `~/.cache` - Optional, saves space

### Wallpaper Rotation (personal profile)

Configure macOS to automatically rotate through wallpapers in a folder at specified intervals.

**Setup:**
1. Create wallpaper folder: `mkdir -p ~/Wallpapers`
2. Add your wallpaper images to `~/Wallpapers`
3. Open System Settings → Wallpaper (or Desktop & Screen Saver on older macOS)
4. Click the "Add Folder" button and select `~/Wallpapers`
5. Enable "Change picture" and set your preferred interval (e.g., every 30 minutes, hourly, daily)

### Backup & Restore (personal profile)

Both backup and restore require NAS connection environment variables:

```bash
export BACKUP_RSYNC_HOST="nas.local"
export BACKUP_RSYNC_USER="username"
export BACKUP_RSYNC_PASS="password"
```

**Backup setup:**
1. System Settings → Privacy & Security → Full Disk Access
2. Click + and add `/usr/sbin/cron`

**Restoring on a fresh machine:**
```bash
uv run ansible-playbook laptop.yml --tags restore
```

## Usage

Run specific parts using tags:

```bash
# Single tag
uv run ansible-playbook laptop.yml --tags dotfiles

# Multiple tags
uv run ansible-playbook laptop.yml --tags vim,terminal

# Skip specific tasks
uv run ansible-playbook laptop.yml --skip-tags dock

# Dry run (see what would change without making changes)
uv run ansible-playbook laptop.yml --check
```

### Available Tags

| Tag | Description |
|-----|-------------|
| `homebrew` | Homebrew packages and casks |
| `mas` | Mac App Store apps |
| `dotfiles` | Copy config files |
| `scripts` | Install utility scripts to ~/.local/bin |
| `vim` | Vim plugins |
| `vscode` | Install VS Code extensions |
| `terminal` | Terminal configuration |
| `dock` | Dock arrangement |
| `macos` | macOS system defaults |
| `backup` | Configure backup cron job |
| `restore` | Restore from NAS backup |

## Customization

Edit `roles/laptop/vars/main.yml` to customize:

- `laptop_base_homebrew_packages` - CLI tools to install
- `laptop_base_homebrew_casks` - GUI applications to install
- `laptop_base_mas_apps` - Mac App Store apps to install
- `laptop_mas_uninstall` - Mac App Store apps to remove
- `laptop_base_dock_apps` - Apps to add to the Dock
- `laptop_dock_remove` - Apps to remove from the Dock
- `laptop_vscode_extensions` - VS Code extensions to install

### Profiles

Variables use a `laptop_base_*` and `laptop_personal_*` naming convention. Base variables apply to all machines, while personal variables add extras for non-work setups. Both are merged at runtime.

## Project Structure

```
laptop.yml                      # Main playbook
roles/laptop/
├── tasks/
│   ├── main.yml               # Task includes
│   ├── homebrew.yml           # Homebrew packages/casks
│   ├── mas.yml                # Mac App Store
│   ├── dotfiles.yml           # Dotfile copies
│   ├── scripts.yml            # Utility scripts
│   ├── vim.yml                # Vim setup
│   ├── vscode.yml             # VS Code extensions
│   ├── terminal.yml           # Terminal profiles
│   ├── dock.yml               # Dock configuration
│   ├── macos.yml              # macOS defaults
│   ├── backup.yml             # Backup cron job (personal)
│   └── restore.yml            # Restore from backup
├── vars/
│   └── main.yml               # All variables
├── files/
│   ├── dotfiles/              # Shell configs (zshrc, vimrc, etc.)
│   ├── scripts/               # Utility scripts (synology-cloudsync-decrypt)
│   ├── vscode/                # VSCode settings
│   ├── JJ.terminal            # Terminal.app profile
│   └── com.googlecode.iterm2.plist  # iTerm2 preferences
├── templates/
│   ├── gitconfig.j2           # Git config template
│   ├── backup.sh.j2           # Backup script
│   └── restore.sh.j2          # Restore script
└── handlers/
    └── main.yml               # Restart Dock, Restart Finder
```

## Development

### Linting

```bash
uv run ansible-lint
uv run pre-commit run --all-files
```

### Upgrading Dependencies

```bash
# Upgrade Python dependencies
uv lock --upgrade && uv sync

# Upgrade pre-commit hooks
uv run pre-commit autoupdate
```
