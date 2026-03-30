# AGENTS.md — sac_music Project Reference

## 1. Project Overview

**sac_music** is a seismic data analysis directory within a polyrepo research workspace at `/Users/ming/Desktop/git_project/`. It contains raw seismic and meteorological data for sonification or analysis.

**Current Files:**
- `TQ07_HHZ_20240403.sac` — Binary SAC (Seismic Analysis Code) waveform file, 34.5 MB. Station TQ07, vertical component (HHZ), collected 2024-04-03.
- `C0H9C0-2024-04-03.csv` — Hourly weather/pressure data from CWA station C0H9C0, 2024-04-03. 24 rows (hourly readings). Columns: ObsTime, StnPres(hPa), Temperature(C), RH(%), WS(m/s), WD(360degree), WSGust(m/s), WDGust(360degree), Precp(mm). Has BOM marker, double-quoted fields, bilingual headers.

**Status:** Data-only directory (not yet a buildable project). May grow into a Python analysis/sonification project. Part of geoscience research workspace (seismology, debris flow, water chemistry, etc.).

## 2. Workspace Conventions

### User-Facing Output Language
- All user-facing output (commits, reviews, chat responses) MUST be in Traditional Chinese (zh-TW).
- Code, variable names, and code comments remain in English.
- See `.copilot-instructions.md` in parent `/git_project/` for term translations.

### Commit Messages
- Follow Conventional Commits 1.0.0 specification.
- Format: `<type>[optional scope]: <description>` — description in Traditional Chinese.
- Types: feat, fix, docs, style, refactor, test, chore, build, ci, perf.
- Example: `feat(sac): 新增 SAC 波形讀取功能`

### Testing
- Always unite related tests in a suite (group by feature/module).

### Code Review
- All review comments in Traditional Chinese.

## 3. Build, Lint, Test Commands

Since this is currently a data-only directory, no build system exists yet. When code is added, use:

```bash
# Python environment (workspace standard)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_reader.py -v

# Run a single test function
python3 -m pytest tests/test_reader.py::test_read_sac_header -v

# Run tests matching a keyword
python3 -m pytest -k "sac" -v
```

**IMPORTANT:** Always use `python3`, never `python`.

**Likely dependencies when code is added:** obspy (SAC file I/O), numpy, pandas, matplotlib, scipy.

## 4. Python Code Style Guidelines

**Imports:** stdlib first (alphabetical), then third-party, then local. No blank lines between groups within a section. One blank line between sections.

**Type Hints:** Always annotate function signatures (params + return). Use modern generics: `dict[str, str]` not `Dict[str, str]`. Use `Optional[X]` for nullable. Use `cast()` from typing for safe coercion.

**Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_CASE for module-level constants. Verb-first for predicates: `is_valid()`, `verify_doi()`.

**Constants:** Define at module top. Use `pathlib.Path` for file paths (preferred over `os.path.join`).

**Error Handling:** Guard clauses with early return. Return default values instead of raising when possible (fail-safe pattern). Broad `except Exception` for external API calls. `finally` for resource cleanup.

**Strings:** f-strings exclusively (no `.format()` or `%`).

**Comments:** Minimal — type hints and names should be self-documenting. Comments explain *why*, not *what*. Use `# --- Section Name ---` dividers for major code sections.

**Docstrings:** Sparse (not required for every function). When used, single-line or Google-style.

**Line Length:** Soft limit ~100 chars. Wrap function signatures at parameters when long.

**CSV Handling:** Use `csv.DictReader`, explicit `encoding="utf-8"`, handle BOM if present.

**JSON:** `json.dump(..., indent=2)` for output, `ensure_ascii=False` for CJK content.

**Logging:** Use `print()` with f-strings for scripts. Use `logging` module for library code.

**Entry Point:** Always include `if __name__ == "__main__": main()` guard.

**No Frameworks:** Use stdlib (urllib, csv, json, pathlib) for simple scripts.

## 5. JavaScript Conventions (if frontend is added)

- Vanilla JS only — no React/Vue/build tools.
- IIFE pattern for module encapsulation: `(function() { 'use strict'; ... })();`
- camelCase for variables/functions, UPPER_CASE for constants.
- Section dividers: `// --- Section Name ---`
- `console.error()` for error logging, early return on failure.
- No TypeScript — plain `.js` files.

## 6. CSS Conventions (if frontend is added)

- CSS custom properties in `:root` for design tokens (colors, fonts, spacing, radii).
- BEM-like naming for component classes.
- Mobile-first responsive design.
- Google Fonts + Feather Icons via CDN only — no heavy framework CDNs.

## 7. Data File Conventions

- **SAC Files:** Binary format, read with ObsPy (`obspy.read()`).
- **CSV Files:** May have BOM (`\ufeff`), bilingual headers, double-quoted fields.
- **Station Naming:** CWA codes (e.g., C0H9C0), seismic codes (e.g., TQ07).
- **Channel Naming:** SEED convention (HHZ = high-gain, high-sample-rate, vertical).
- **File Naming Pattern:** `{station}_{channel}_{YYYYMMDD}.sac`, `{station}-{YYYY-MM-DD}.csv`.

## 8. Anti-Patterns

- NEVER use `python` — always `python3`.
- NEVER suppress type errors with `as any`, `@ts-ignore`, or `# type: ignore`.
- NEVER commit `.env` files or API keys.
- NEVER edit auto-generated files.
- NEVER add heavy CDN/framework dependencies for simple tasks.
- NEVER leave non-sequential IDs after deletion — renumber immediately.
- NEVER use `os.path` when `pathlib.Path` works.

## 9. Seismic Data Quick Reference

### Reading SAC Files (ObsPy)
```python
from obspy import read

st = read("TQ07_HHZ_20240403.sac")
tr = st[0]  # first (and typically only) trace
data = tr.data  # numpy array of amplitudes
header = tr.stats  # metadata: sampling_rate, npts, starttime, etc.
```

### Reading the CSV (with BOM handling)
```python
import csv
from pathlib import Path

csv_path = Path("C0H9C0-2024-04-03.csv")
with open(csv_path, encoding="utf-8-sig") as f:
    next(f)  # skip Chinese header row
    reader = csv.DictReader(f)
    rows = list(reader)
# rows[0] = {"ObsTime": "01", "StnPres": "678.7", ...}
```

### Key Metadata
- **Sampling rate** (HHZ): Typically 100 Hz (check `tr.stats.sampling_rate`)
- **Station TQ07**: Taiwan broadband seismic station
- **Station C0H9C0**: CWA (Central Weather Administration) surface weather station
- **Date**: 2024-04-03 — the day of the Hualien earthquake (ML 7.2)

