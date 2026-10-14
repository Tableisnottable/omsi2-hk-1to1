# Copilot Instructions — OMSI 2 Hong Kong 1:1 Map (omsi2-hk-1to1)

Guidance for working effectively in this repository. It builds a 1:1 scale Hong Kong map for OMSI 2 under the HP1C scheme.

## Repository layout at a glance

| Path | Purpose |
|------|---------|
| `maps/HK_HP1C_<code>/` | One OMSI 2 map tile-set per district code (CW, WCH, EAS, SOU, YTM, SSP, KCT, WTS, KTN, KWT, TWW, TMM, YLN, NTH, TPO, STN, SKG, ISL, HZMB). Each holds `global.cfg`, `tile_0_0.map`, `drivers.txt`, `parklist_p.txt`, `ailists.cfg`. |
| `src/scripts/` | PowerShell helpers: `Generate-Sco.ps1` (`.o3d` → `.sco` scenery objects), `Generate-Hof.ps1` (route `.hof` file), `Build-Release.ps1` (zips `maps` + `Sceneryobjects` + `Vehicles` into `release/`), `Run-OpenOmsi.ps1`. |
| `setup.ps1` | One-time scaffolding: creates the directory tree, all map folders with stub configs, and generates the `src/scripts/` helpers. Hardcodes the author's local path (`C:\Users\Table\Documents\GitHub\omsi2-hk-1to1`) — update the `$RepoPath` variable when running elsewhere. |
| `release/` | Generated release zips (gitignored: `release/*.zip`). Treat as derived data. |

## Build / scripts

There is **no test or lint suite**. Validation is manual (script exit codes, in-game checks in OMSI 2).

```powershell
# One-time scaffold (updates $RepoPath first if needed)
powershell -File setup.ps1

# Regenerate scenery-object .sco files from .o3d models
powershell -File src\scripts\Generate-Sco.ps1

# Regenerate route file
powershell -File src\scripts\Generate-Hof.ps1

# Package a release zip
powershell -File src\scripts\Build-Release.ps1
```

## Non-obvious conventions

- **Windows-only PowerShell tooling** with hardcoded author-local paths. Scripts resolve relative to `$PSScriptRoot`; keep that pattern when adding new scripts.
- **OMSI 2 config formats are positional/line-based** (`global.cfg`, `tile_*.map`, `ailists.cfg`, `.hof`). Preserve exact section headers (`[name]`, `[map]`, `[ailist]`, …) and line order — the game parser is strict.
- **Gitignored outputs**: `*.bak`, `*.tmp`, `*.log`, `*.fbx`, `*.obj`, `release/*.zip`. Never commit these.
- **Bilingual content**: stop names and descriptions mix English and Traditional Chinese. Preserve existing language per file.

## Task execution: small steps, auto commit and push

- Break every request into small, independently committable steps (one logical change per step: e.g. one script, one map tile, one doc update). Finish and verify one step before starting the next.
- Automatically commit after each verified step with conventional prefixes (`feat:`, `fix:`, `docs:`, `refactor:`) — do not ask for confirmation first.
- Automatically push to the current working branch after committing so work is backed up in the repo. Do not push directly to `main` — use the session branch and open a pull request for review.
- Never combine unrelated changes in one commit, and never leave finished work uncommitted at the end of a session.
- Exception — large files are never auto-committed: do not commit or push files larger than 10 MB or binary build artifacts (`.o3d`/model files, textures, `.fbx`, `.obj`, release `.zip` files). Leave them uncommitted and tell the user, so they can decide. Small text, config, and code changes always go through the automatic path above.
