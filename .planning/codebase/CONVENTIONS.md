# Coding Conventions

**Analysis Date:** 2026-02-24

## Naming Patterns

**Files:**
- Command files: kebab-case with hyphens (e.g., `gsd-check-update.js`, `gsd-statusline.js`)
- Module files: camelCase (e.g., `core.cjs`, `state.cjs`, `phase.cjs`)
- Markdown documentation: UPPERCASE with hyphens (e.g., `STATE.md`, `ROADMAP.md`, `map-codebase.md`)
- Configuration files: hyphenated or JSON (e.g., `config.json`, `settings.json`)

**Functions:**
- Command functions: prefixed with `cmd` followed by PascalCase action (e.g., `cmdStateLoad`, `cmdPhaseNextDecimal`, `cmdVerifySummary`)
- Helper functions: camelCase with descriptive verbs (e.g., `loadConfig`, `safeReadFile`, `execGit`, `extractFrontmatter`)
- Boolean test functions: start with `is` or `has` (e.g., `isGitIgnored`, `hasDone`, `hasFiles`)

**Variables:**
- Constants in UPPER_SNAKE_CASE: `MODEL_PROFILES`, `WARNING_THRESHOLD`, `CRITICAL_THRESHOLD`, `STALE_SECONDS`, `DEBOUNCE_CALLS`
- Regular variables in camelCase: `cwd`, `filePath`, `phaseNum`, `phase_name`, `phaseName` (underscore for response fields, camelCase for local)
- Collections use descriptive plurals: `dirs`, `files`, `entries`, `summaries`, `plans`, `incompletePlans`

**Types:**
- Object keys use snake_case when representing structured data (response objects, JSON fields): `phase_number`, `phase_name`, `incomplete_plans`, `user_id`
- In-memory variables use camelCase: `phaseNumber`, `phaseName`

## Code Style

**Formatting:**
- No automated formatter detected (eslint/prettier not configured)
- 2-space indentation throughout (observed in all `.cjs` files)
- Lines break at approximately 100 characters when displaying long patterns
- Spacing: one blank line between logical sections within functions

**Linting:**
- No `.eslintrc` or linting configuration file detected
- Code style enforced implicitly through consistency and code review
- Patterns suggest Node.js best practices without strict linting

**CommonJS Pattern:**
- All modules use `require()` for imports
- All modules use `module.exports` for exports
- `.cjs` file extension explicitly marks CommonJS modules

## Import Organization

**Order:**
1. Native Node.js modules: `require('fs')`, `require('path')`, `require('child_process')`, `require('os')`
2. Custom modules: `require('./lib/core.cjs')`, `require('./lib/state.cjs')`
3. Destructured imports when multiple items: `const { error, output, loadConfig } = require('./core.cjs')`

**Path Style:**
- Relative imports use explicit paths: `./lib/core.cjs` not `./lib`
- Full module names without index shortcuts
- Alphabetical ordering within each section

**Example from `gsd-tools.cjs`:**
```javascript
const { error } = require('./lib/core.cjs');
const state = require('./lib/state.cjs');
const phase = require('./lib/phase.cjs');
const roadmap = require('./lib/roadmap.cjs');
```

## Error Handling

**Patterns:**
- Two-level error strategy: hard errors via `error()` function vs. graceful null returns
- Hard errors: `error('message')` exits with code 1 and writes to stderr, used for CLI argument validation
- Graceful errors: `return null` or empty objects wrapped in try-catch blocks for file operations
- `safeReadFile()` utility returns `null` on any read error (file missing, permission denied, etc.)
- Error functions like `cmdStateLoad()` output `{ error: 'message' }` JSON when graceful handling needed

**Pattern example from `state.cjs`:**
```javascript
function cmdStateLoad(cwd, raw) {
  let stateRaw = '';
  try {
    stateRaw = fs.readFileSync(path.join(planningDir, 'STATE.md'), 'utf-8');
  } catch {}  // Silent fail - returns empty string if missing

  if (!fs.existsSync(fullPath)) {
    output({ error: 'STATE.md not found' }, raw);
    return;
  }
}
```

## Logging

**Framework:** Console and structured JSON output

**Patterns:**
- No traditional logging library; uses `process.stdout.write()` and `process.stderr.write()`
- All command outputs serialized to JSON via `output()` helper in `core.cjs`
- Errors written to stderr: `process.stderr.write('Error: ' + message + '\n')`
- Large JSON payloads (>50KB) written to temp files with `@file:` prefix to avoid buffer overflow
- Silent failures preferred over console spam: try-catch blocks often empty (`catch {}`)

**Example from `gsd-statusline.js`:**
```javascript
try {
  const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
  if (cache.update_available) {
    gsdUpdate = '\x1b[33m⬆ /gsd:update\x1b[0m │ ';
  }
} catch (e) {
  // Silently fail on file system errors - don't break statusline
}
```

## Comments

**When to Comment:**
- File-level comments describe module purpose and exports (every `.cjs` file opens with `/** * Module Name — Description */`)
- Section delimiters using `// ─── Section Name ───────────────────────────────────────────────────────`
- Inline comments for non-obvious regex patterns, magic numbers, and workarounds
- No over-commenting: most code is self-documenting via function/variable names

**JSDoc/TSDoc:**
- Minimal JSDoc usage
- Command files (hooks) use shebang and initial comment block: `#!/usr/bin/env node` followed by `// Description`
- No formal type annotations (vanilla JavaScript, no TypeScript)

**Example from `gsd-context-monitor.js`:**
```javascript
#!/usr/bin/env node
// Context Monitor - PostToolUse hook
// Reads context metrics from the statusline bridge file and injects
// warnings when context usage is high.
//
// How it works:
// 1. The statusline hook writes metrics to /tmp/claude-ctx-{session_id}.json
// 2. This hook reads those metrics after each tool use
// 3. When remaining context drops below thresholds, it injects a warning
```

## Function Design

**Size:**
- Small, focused functions (most 10-50 lines)
- Utilities average 20 lines
- Command handlers (`cmd*`) average 30-80 lines depending on complexity
- Complex operations split into helper functions

**Parameters:**
- Command functions consistently take `(cwd, options, raw)` or `(cwd, field, value)` pattern
- Minimal parameter overloading; prefer options objects: `{ phase, plan, duration, tasks, files }`
- File I/O helpers use single path parameter

**Return Values:**
- Most functions return nothing (side effects: write files, call `output()`)
- Query functions return objects: `{ found: true, directory: '...', phase_number: '01' }`
- Utilities return parsed data or null: `safeReadFile()` returns string or null
- No promises/async: all synchronous Node.js with blocking I/O

**Example from `phase.cjs`:**
```javascript
function cmdPhaseNextDecimal(cwd, basePhase, raw) {
  // Takes cwd and single parameter, uses local variables for options
  const phasesDir = path.join(cwd, '.planning', 'phases');
  const normalized = normalizePhaseName(basePhase);

  // Early return for missing directory
  if (!fs.existsSync(phasesDir)) {
    output({ found: false, base_phase: normalized, next: `${normalized}.1` }, raw, `${normalized}.1`);
    return;
  }

  // Logic here
}
```

## Module Design

**Exports:**
- Each `.cjs` file exports an object with named command functions and helpers
- Main entry point `gsd-tools.cjs` imports all modules and routes CLI commands via switch statement
- No default exports; all modules use named exports

**Barrel Files:**
- No barrel files used
- All imports from specific module files: `require('./lib/core.cjs')` not `require('./lib')`

**Example from module exports:**
```javascript
// At end of core.cjs:
module.exports = {
  output, error, safeReadFile, loadConfig, isGitIgnored,
  execGit, normalizePhaseName, comparePhaseNum, findPhaseInternal,
  MODEL_PROFILES, // Constants exported
  // ... more functions
};

// Usage in gsd-tools.cjs:
const { error } = require('./lib/core.cjs');
const state = require('./lib/state.cjs');
```

## CLI Pattern

**Command Structure:**
- CLI routing via switch statement on first argument (command name)
- Subcommands handled as nested switches: `case 'state': { const subcommand = args[1]; ... }`
- All numeric arguments parsed via `parseInt(args[idx + 1], 10)` with base 10 specified
- Optional flag parsing via `.indexOf()`: `const idx = args.indexOf('--flag'); const val = idx !== -1 ? args[idx + 1] : default;`

**Output Handling:**
- All output through `output(result, raw, rawValue)` function
- JSON output by default; `--raw` flag outputs plain text value only
- For large payloads, write to tmpfile and prefix with `@file:`

---

*Convention analysis: 2026-02-24*
