# External Integrations

**Analysis Date:** 2026-02-24

## APIs & External Services

**Web Search:**
- Brave Search API - Optional web search for phase research
  - Integration method: REST API via native Node.js `fetch()`
  - Auth: Bearer token in `BRAVE_API_KEY` env var or `~/.gsd/brave_api_key` file
  - Endpoint: `https://api.search.brave.com/res/v1/web/search`
  - Implementation: `cmdWebSearch()` in `.claude/get-shit-done/bin/lib/commands.cjs`
  - Parameters: `query`, `limit` (default depends on config), `freshness` (day|week|month)
  - Response format: JSON web results
  - Enabled: Only if `BRAVE_API_KEY` available and `brave_search: true` in `.planning/config.json`

## Data Storage

**File Storage:**
- Local filesystem only - All state and configuration stored locally
  - Project root: `.planning/` directory structure
    - `.planning/config.json` - Project configuration
    - `.planning/phases/` - Phase directories and work files
    - `.planning/codebase/` - Codebase analysis documents (STACK.md, ARCHITECTURE.md, etc.)
    - `.planning/todos/` - Task management

**Configuration Files:**
- `.planning/config.json` - Per-project settings (model profiles, workflow options, Brave Search toggle)
- `~/.gsd/defaults.json` - User-level default configuration (applied to all projects)
- `~/.gsd/brave_api_key` - Optional fallback location for Brave Search API key

**State Management:**
- Markdown files with YAML frontmatter (no database required)
  - `ROADMAP.md` - Project roadmap with phase descriptions
  - `STATE.md` - Current project state and metadata
  - `REQUIREMENTS.md` - Project requirements tracking
  - `MILESTONES.md` - Completed milestones archive

**Caching:**
- Version check cache: `~/.claude/cache/gsd-update-check.json`
  - Updated asynchronously on session start
  - Checked via npm registry for `get-shit-done-cc` package updates

## Version Control

**Git Integration:**
- Primary: Git command execution via `execSync()` for all VCS operations
  - Commit hooks: `.claude/hooks/` (run on SessionStart and PostToolUse)
  - Workflow: Automatic commits to `.planning/` documents
  - Branch templates: Configurable in `.planning/config.json`
    - `phase_branch_template`: `gsd/phase-{phase}-{slug}` (default)
    - `milestone_branch_template`: `gsd/{milestone}-{slug}` (default)
  - Implementation: `execGit()` helper in `.claude/get-shit-done/bin/lib/core.cjs`

- Git ignore check: `git check-ignore` via `isGitIgnored()` for filtering files

**Deployment/Installation:**
- Package distribution: Published to npm registry as `get-shit-done-cc`
- Version tracking: `.claude/get-shit-done/VERSION` file (semantic version 1.20.6)
- Update checking: Async background check via `gsd-check-update.js` hook
  - Compares installed version vs npm registry
  - Results cached to `~/.claude/cache/gsd-update-check.json`

## Authentication & Identity

**Optional API Auth:**
- Brave Search API - Bearer token authentication
  - Where stored: Environment variable `BRAVE_API_KEY` or `~/.gsd/brave_api_key`
  - Secret management: User manages (not stored in .planning/)
  - No OAuth or session management

**No user authentication:**
- GSD is local CLI tool, no user login required
- No session tokens or identity management
- Configuration per-project basis only

## Webhooks & Callbacks

**Incoming:**
- None - GSD is stateless CLI without server endpoints

**Outgoing:**
- None - GSD dispatches work to Claude agents via prompt/Claude Code; no callbacks

## Agent Coordination

**Claude Integration (Not External APIs):**
- Dispatches work to Claude AI agents via markdown prompts
- Agent types with model profile mappings in `.claude/get-shit-done/bin/lib/core.cjs`:
  - `gsd-planner` - Opus (quality), Opus (balanced), Sonnet (budget)
  - `gsd-executor` - Opus (quality), Sonnet (balanced/budget)
  - `gsd-phase-researcher` - Opus (quality), Sonnet (balanced), Haiku (budget)
  - `gsd-project-researcher` - Opus (quality), Sonnet (balanced), Haiku (budget)
  - `gsd-research-synthesizer` - Sonnet (quality/balanced), Haiku (budget)
  - `gsd-debugger` - Opus (quality), Sonnet (balanced/budget)
  - `gsd-codebase-mapper` - Sonnet (quality), Haiku (balanced/budget)
  - `gsd-verifier` - Sonnet (quality/balanced), Haiku (budget)
  - `gsd-plan-checker` - Sonnet (quality/balanced), Haiku (budget)
  - `gsd-integration-checker` - Sonnet (quality/balanced), Haiku (budget)
  - `gsd-roadmapper` - Opus (quality), Sonnet (balanced/budget)

- Model profile selection: Configured in `.planning/config.json` via `model_profile` field
  - `quality` - Best output, higher cost (Opus models)
  - `balanced` - Good quality at reasonable cost (Sonnet models)
  - `budget` - Fastest/cheapest (Haiku models)

## Environment Configuration

**Development:**
- Required env vars: None mandatory
- Optional env vars: `BRAVE_API_KEY` (for web search)
- Secrets location: `~/.gsd/brave_api_key` file (gitignored)
- Working directory: Project root with `.claude/` subdirectory

**Project Initialization:**
- Generates `.planning/config.json` on first use via `config-ensure-section`
- Auto-detects Brave API key availability and enables `brave_search` if present
- Creates directory structure: `.planning/phases/`, `.planning/todos/`, `.planning/codebase/`

**Configuration Override Hierarchy:**
1. User-level defaults: `~/.gsd/defaults.json` (if exists)
2. Hardcoded defaults in `.claude/get-shit-done/bin/lib/config.cjs`
3. Project-level overrides: `.planning/config.json`

## Key Configuration Parameters

**Workflow Control:**
- `model_profile` - Which Claude models to use (quality|balanced|budget)
- `commit_docs` - Auto-commit planning documents to git
- `search_gitignored` - Include .gitignored files in codebase analysis
- `branching_strategy` - Git branching approach (none|phases|milestones)
- `research` - Enable phase research agent
- `plan_checker` - Enable plan validation agent
- `verifier` - Enable work verification agent
- `parallelization` - Run multiple agents in parallel when possible
- `brave_search` - Enable Brave Search API for research (if API key present)

## No Third-Party Dependencies

**Important:** Unlike typical Node.js projects:
- No npm packages installed (no node_modules)
- No external SDKs or client libraries
- All file I/O via Node.js `fs` module
- Git is only external executable dependency
- All other operations pure Node.js

---

*Integration audit: 2026-02-24*
*Update when adding/removing external services or changing API endpoints*
