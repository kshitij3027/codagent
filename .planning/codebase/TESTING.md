# Testing Patterns

**Analysis Date:** 2026-02-24

## Test Framework

**Runner:**
- No test runner detected (Jest, Mocha, Vitest not configured)
- No test files (`.test.js`, `.spec.js`) found in codebase

**Assertion Library:**
- No assertion library in use

**Run Commands:**
- Not applicable — no automated tests configured

## Test File Organization

**Location:**
- Not detected — testing not implemented in this codebase

**Naming:**
- Not applicable

**Structure:**
- Not applicable

## Test Structure

**Current State:**
- This is a utility framework codebase focused on GSD (Get Shit Done) workflow automation
- No unit or integration tests present
- Code quality and correctness enforced through:
  - Code review and manual validation
  - Inline error handling (try-catch with graceful fallbacks)
  - Staged rollout of commands

**Validation Mechanisms:**
- `cmdVerifySummary()` in `verify.cjs` performs runtime validation of SUMMARY.md structure
- `cmdVerifyPlanStructure()` validates PLAN.md frontmatter and XML task elements
- `cmdVerifyPhaseCompleteness()` checks phase directory consistency
- `validate consistency` command verifies phase numbering and disk/roadmap sync
- `validate health` command checks .planning/ integrity with optional repair

**Example from `verify.cjs` - Runtime Validation Pattern:**
```javascript
function cmdVerifySummary(cwd, summaryPath, checkFileCount, raw) {
  // Check 1: File existence
  if (!fs.existsSync(fullPath)) {
    output({ passed: false, checks: { summary_exists: false }, errors: ['SUMMARY.md not found'] }, raw, 'failed');
    return;
  }

  // Check 2: Spot-check referenced files
  const mentionedFiles = new Set();
  const patterns = [/`([^`]+\.[a-zA-Z]+)`/g];
  for (const pattern of patterns) {
    let m;
    while ((m = pattern.exec(content)) !== null) {
      mentionedFiles.add(m[1]);
    }
  }

  // Check 3: Git commit verification
  const commitHashPattern = /\b[0-9a-f]{7,40}\b/g;
  const hashes = content.match(commitHashPattern) || [];
  let commitsExist = false;
  if (hashes.length > 0) {
    for (const hash of hashes.slice(0, 3)) {
      const result = execGit(cwd, ['cat-file', '-t', hash]);
      if (result.exitCode === 0 && result.stdout === 'commit') {
        commitsExist = true; break;
      }
    }
  }
}
```

## Mocking

**Framework:**
- Not applicable — no testing framework configured

**Patterns:**
- File system operations use `fs.existsSync()`, `fs.readFileSync()`, `fs.writeFileSync()` without mocking
- Git operations wrapped in `execGit()` helper that captures exit codes and output
- Network calls (optional Brave Search API) wrapped in try-catch with silent failures
- Test execution would require mocking filesystem and git, but no test harness exists

**What to Mock (if tests were added):**
- `fs` module for file I/O testing
- `execSync` for git/subprocess calls
- `process.stdout.write()` and `process.stderr.write()` for output capture
- Path resolution functions with different directory structures

**What NOT to Mock:**
- Core business logic (phase numbering, slug generation, config loading)
- Actual file content parsing (YAML frontmatter extraction, markdown structure)

## Fixtures and Factories

**Test Data:**
- Not implemented; no fixtures directory exists
- All data flows from real files in `.planning/` directory structure
- Test scenarios would need to create temporary `.planning/` structures with valid PLAN.md, SUMMARY.md, etc.

**Location:**
- Not applicable — no fixtures present

**Example fixture approach (for future tests):**
```javascript
// Would create temporary phase directory with valid structure
const fixturePhase = {
  directory: '.planning/phases/01-Initialize-Project',
  files: {
    'PLAN.md': '---\nphase: 1\nplan: 1\n---\n<task>...',
    'SUMMARY.md': '---\nphase: 1\nplan: 1\n---\n## Summary'
  }
};
```

## Coverage

**Requirements:**
- No coverage targets or tools configured
- Code coverage not measured

**View Coverage:**
- Not applicable

## Test Types

**Unit Tests:**
- Not implemented
- Would test individual functions like:
  - `normalizePhaseName('1')` → `'01'`
  - `generateSlug('My Test Phase')` → `'my-test-phase'`
  - `comparePhaseNum('01', '01A')` → -1
  - `extractFrontmatter(markdown)` → object

**Integration Tests:**
- Not implemented
- Would test workflows like:
  - `state update` → reads STATE.md, modifies field, writes back
  - `phase add` → updates ROADMAP.md, creates directory, returns path
  - `verify phase-completeness` → reads phase directory, checks plan/summary pairing

**E2E Tests:**
- Not implemented
- Would test command-line workflows end-to-end:
  - `node gsd-tools.cjs state load` → output valid JSON
  - `node gsd-tools.cjs phase add --description "Test"` → creates phase directory

## Hook-Based Testing

**Post-Tool Validation:**
The codebase includes runtime hook validation for critical workflows:

**`gsd-context-monitor.js` (PostToolUse hook):**
- Monitors context window usage
- Injects warnings when remaining ≤ 35% (WARNING) or ≤ 25% (CRITICAL)
- Debounces warnings to avoid spam (5 tool calls between warnings)
- Reads metrics from statusline bridge file and updates debounce state
- Pattern: checks preconditions and exits silently if not applicable
```javascript
// Silent exit on missing preconditions
if (!sessionId) { process.exit(0); }
if (!fs.existsSync(metricsPath)) { process.exit(0); }

// Debounce logic
if (!firstWarn && warnData.callsSinceWarn < DEBOUNCE_CALLS && !severityEscalated) {
  fs.writeFileSync(warnPath, JSON.stringify(warnData));
  process.exit(0);
}
```

**`gsd-statusline.js` (Statusline hook):**
- Reads JSON input from stdin
- Validates context window metrics
- Writes bridge file for context monitor
- Gracefully handles parse errors with try-catch
- Outputs ANSI-colored statusline to stdout

## Error Handling in Operations

**File Operations:**
- Wrapped in try-catch with context-specific handling
- `safeReadFile()` returns null on any error (preferred for optional reads)
- Command handlers output error objects rather than throwing
```javascript
try {
  const content = fs.readFileSync(filePath, 'utf-8');
} catch {
  error('File not found');  // Hard exit
}
```

**Git Operations:**
- Wrapped in `execGit()` helper that never throws
- Returns `{ exitCode, stdout, stderr }` for caller inspection
- Safe for commands that may legitimately fail (e.g., `git check-ignore`)

## Validation Patterns

**Frontmatter Validation:**
```javascript
// From verify.cjs - cmdVerifyPlanStructure
const required = ['phase', 'plan', 'type', 'wave', 'depends_on', 'files_modified', 'autonomous', 'must_haves'];
for (const field of required) {
  if (fm[field] === undefined) errors.push(`Missing required frontmatter field: ${field}`);
}
```

**XML Task Structure Validation:**
```javascript
const taskPattern = /<task[^>]*>([\s\S]*?)<\/task>/g;
const tasks = [];
let taskMatch;
while ((taskMatch = taskPattern.exec(content)) !== null) {
  const taskContent = taskMatch[1];
  const nameMatch = taskContent.match(/<name>([\s\S]*?)<\/name>/);
  if (!nameMatch) errors.push('Task missing <name> element');
  if (!/<action>/.test(taskContent)) errors.push(`Task missing <action>`);
}
```

**Consistency Checks:**
```javascript
// Wave/depends_on consistency
if (fm.wave && parseInt(fm.wave) > 1 && (!fm.depends_on || fm.depends_on.length === 0)) {
  warnings.push('Wave > 1 but depends_on is empty');
}

// Autonomous/checkpoint consistency
const hasCheckpoints = /<task\s+type=["']?checkpoint/.test(content);
if (hasCheckpoints && fm.autonomous !== 'false') {
  errors.push('Has checkpoint tasks but autonomous is not false');
}
```

---

*Testing analysis: 2026-02-24*
