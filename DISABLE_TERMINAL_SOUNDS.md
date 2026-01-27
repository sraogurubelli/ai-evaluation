# Disable Terminal Sounds in Cursor

Cursor/terminal sounds are usually caused by the terminal bell (beep) that plays when:
- Commands complete
- Errors occur
- Long-running commands finish
- Terminal receives certain control characters

## Quick Fixes

### Option 1: Disable in Cursor Settings (Recommended)
1. Open Cursor Settings (`Cmd+,` on Mac, `Ctrl+,` on Windows/Linux)
2. Search for "terminal bell" or "bell"
3. Uncheck "Terminal: Enable Bell" or set "Terminal: Bell Duration" to 0

### Option 2: Disable in Shell Config
Add to your `~/.zshrc` (Mac default) or `~/.bashrc`:

```bash
# Disable terminal bell
set bell-style none

# Or for zsh
unsetopt beep
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Option 3: Disable System-Wide (macOS)
```bash
# Disable system beep sound
defaults write com.apple.sound.beep.plist -int 0
```

### Option 4: Taskfile Silent Mode
If sounds are coming from task completion, you can make tasks quieter by removing echo statements or redirecting output.

## Verify
After making changes, restart Cursor and run a command. You should no longer hear sounds.

## Common Causes
- Terminal bell on command completion
- Error beeps when commands fail
- System notification sounds
- Task completion notifications

## Cursor-Specific Settings
Look for these in Cursor Settings:
- `terminal.integrated.enableBell`
- `terminal.integrated.bellDuration`
- `workbench.settings.enableNaturalLanguageSearch` (to find settings easier)
