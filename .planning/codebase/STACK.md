# Technology Stack

**Analysis Date:** 2026-02-24

## Languages

**Primary:**
- JavaScript (CommonJS) - All executable scripts and CLI tools

**Secondary:**
- Markdown - Documentation, templates, command definitions, workflows, agent specifications

## Runtime

**Environment:**
- Node.js v25.4.0 (LTS compatible, v20.x minimum recommended)
- No browser runtime (CLI/Node.js only)

**Package Manager:**
- npm 11.7.0
- Lockfile: `package.json` minimal (CommonJS only)

## Frameworks

**Core:**
- None - Vanilla Node.js CLI without frameworks
- Native Node.js APIs: `fs`, `path`, `child_process`, `os` for all operations

**Build/Dev:**
- None required - CommonJS executes directly without compilation

**Version/Release Management:**
- VERSION file: `.claude/get-shit-done/VERSION` - Contains semantic version (current: 1.20.6)

## Key Dependencies

**Critical:**
- **Node.js built-ins only** - No external npm packages used
  - `fs` - File system operations (read/write/sync)
  - `path` - Path manipulation and normalization
  - `child_process` (execSync, spawn) - Git commands, subprocess execution
  - `os` - Home directory, temp directory access

**Infrastructure:**
- Git - External executable via `execSync` for version control operations
- Brave Search API - Optional external service for web search functionality

## Configuration

**Environment:**
- Configured via JSON: `.planning/config.json` (created per project)
- Optional env vars:
  - `BRAVE_API_KEY` - Optional Brave Search API key for research capabilities
  - `BRAVE_API_KEY` also checked in `~/.gsd/brave_api_key` fallback file

**Build:**
- No build configuration needed (CommonJS executes directly)
- No tsconfig.json, eslint, prettier, or other tooling

## Architecture

**CLI Entry Point:**
- `./claude/get-shit-done/bin/gsd-tools.cjs` - Main executable (Node.js shebang)
- Run via: `node gsd-tools.cjs <command> [args] [--raw]`

**Module Structure:**
- Monolithic CLI with modular lib structure
- Library modules in `.claude/get-shit-done/bin/lib/`:
  - `core.cjs` - Shared utilities, constants, helpers, model profiles
  - `commands.cjs` - Standalone atomic operations (18KB)
  - `state.cjs` - STATE.md file operations
  - `phase.cjs` - Phase management (phase number calculations, directory operations)
  - `roadmap.cjs` - ROADMAP.md operations
  - `verify.cjs` - Verification and validation logic
  - `config.cjs` - Planning config CRUD operations
  - `template.cjs` - Template generation
  - `milestone.cjs` - Milestone operations
  - `init.cjs` - Project initialization
  - `frontmatter.cjs` - Markdown frontmatter parsing

**Hooks & Monitoring:**
- `.claude/hooks/` - Session hooks (Node.js scripts)
  - `gsd-check-update.js` - Background version checking (npm registry)
  - `gsd-statusline.js` - Status line generation
  - `gsd-context-monitor.js` - Context monitoring

## Platform Requirements

**Development:**
- macOS/Linux/Windows (any platform with Node.js v20+)
- No external tools required (all Node.js built-ins)
- Git must be available in PATH for version control operations

**Production/Deployment:**
- Installed locally via npm (distributed as package)
- Configuration: `.planning/config.json` per project in `.claude/` or root
- Brave Search API key optional for enhanced research capabilities
- No database, server, or long-running processes

## Key Characteristics

- **Zero external dependencies** - Uses only Node.js standard library
- **Stateless CLI** - All state persisted to markdown files (.planning/, ROADMAP.md, STATE.md)
- **Git-aware** - Integrates with git for version control operations via execSync
- **Optional web search** - Brave Search API integration if BRAVE_API_KEY configured
- **Markdown-first** - Configuration and state stored as markdown with frontmatter
- **Multi-agent coordination** - Dispatches work to Claude agents via prompts
- **Self-hosting compatible** - Single executable, no external dependencies

---

*Stack analysis: 2026-02-24*
*Update after runtime version changes or new external service integrations*
