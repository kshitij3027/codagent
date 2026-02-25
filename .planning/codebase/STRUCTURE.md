# Codebase Structure

**Analysis Date:** 2026-02-24

## Directory Layout

```
.claude/
├── agents/                          # Agent prompt definitions (11 agents)
│   ├── gsd-codebase-mapper.md      # Analyze codebase (tech/arch/quality/concerns)
│   ├── gsd-debugger.md             # Debug execution failures
│   ├── gsd-executor.md             # Execute plans atomically
│   ├── gsd-integration-checker.md  # Verify external integrations
│   ├── gsd-phase-researcher.md     # Research phase-specific tech
│   ├── gsd-plan-checker.md         # Verify plans achieve goal
│   ├── gsd-planner.md              # Create executable task plans
│   ├── gsd-project-researcher.md   # Research domain before roadmap
│   ├── gsd-research-synthesizer.md # Aggregate research findings
│   ├── gsd-roadmapper.md           # Transform requirements → phases
│   └── gsd-verifier.md             # Verify goal achievement
├── commands/gsd/                    # User-facing CLI commands (32 commands)
│   ├── new-project.md              # Initialize project
│   ├── plan-phase.md               # Create phase plan
│   ├── execute-phase.md            # Execute phase plans
│   ├── research-phase.md           # Research phase
│   ├── verify-work.md              # Verify phase goal
│   ├── map-codebase.md             # Map codebase analysis
│   ├── add-phase.md                # Insert phase
│   ├── complete-milestone.md       # Mark milestone done
│   └── [28 more workflow commands]
├── get-shit-done/
│   ├── bin/
│   │   ├── gsd-tools.cjs           # Main CLI tool
│   │   └── lib/                    # Core utilities
│   │       ├── core.cjs            # Model profiles, output, file utils
│   │       ├── state.cjs           # STATE.md management
│   │       ├── phase.cjs           # Phase queries
│   │       ├── roadmap.cjs         # Roadmap queries
│   │       ├── milestone.cjs       # Milestone state
│   │       ├── commands.cjs        # Argument parsing
│   │       ├── frontmatter.cjs     # YAML parsing
│   │       ├── verify.cjs          # Verification results
│   │       ├── template.cjs        # Template loading
│   │       ├── init.cjs            # Initialization
│   │       └── config.cjs          # Config management
│   ├── workflows/                  # Multi-agent workflow orchestration (27 workflows)
│   │   ├── new-project.md          # Unified project init
│   │   ├── plan-phase.md           # Plan → Verify loop
│   │   ├── execute-phase.md        # Wave-based execution
│   │   ├── research-phase.md       # Phase research
│   │   ├── verify-work.md          # Verification + gap closure
│   │   └── [22 more management workflows]
│   ├── references/                 # Decision frameworks & guides (15 references)
│   │   ├── questioning.md          # Project scoping questions
│   │   ├── model-profiles.md       # Model selection guidance
│   │   ├── planning-config.md      # Configuration reference
│   │   ├── git-integration.md      # Git workflow principles
│   │   ├── ui-brand.md             # Output formatting
│   │   ├── tdd.md                  # Test-driven development
│   │   └── [9 more reference docs]
│   ├── templates/                  # Template files
│   │   ├── project.md              # Project template
│   │   ├── requirements.md         # Requirements template
│   │   ├── roadmap.md              # Roadmap template
│   │   ├── milestone.md            # Milestone template
│   │   ├── phase-prompt.md         # Phase context template
│   │   ├── codebase/
│   │   │   ├── architecture.md     # ARCHITECTURE.md template
│   │   │   ├── structure.md        # STRUCTURE.md template
│   │   │   ├── stack.md            # STACK.md template
│   │   │   ├── integrations.md     # INTEGRATIONS.md template
│   │   │   ├── conventions.md      # CONVENTIONS.md template
│   │   │   ├── testing.md          # TESTING.md template
│   │   │   └── concerns.md         # CONCERNS.md template
│   │   └── [more templates]
│   └── VERSION                     # GSD framework version
├── hooks/                          # Claude session hooks
│   ├── gsd-check-update.js        # Check for GSD updates at session start
│   ├── gsd-statusline.js          # Display project status
│   └── gsd-context-monitor.js     # Monitor context usage
├── skills/                         # Reusable pattern libraries (4 skills)
│   ├── just/
│   │   ├── SKILL.md               # Just command runner skill
│   │   └── examples/              # Justfile templates
│   ├── orchestration/
│   │   └── SKILL.md               # Delegation patterns
│   ├── commit-workflow/
│   │   └── SKILL.md               # Git commit conventions
│   └── testing-with-docker/
│       └── SKILL.md               # E2E testing patterns
├── settings.json                  # Session hooks configuration
├── gsd-file-manifest.json        # File integrity hashes
└── package.json                   # CommonJS module marker

.planning/                          # Project state (created at init)
├── PROJECT.md                     # Project vision & scope
├── REQUIREMENTS.md                # Feature requirements
├── ROADMAP.md                     # Phase definitions
├── STATE.md                       # Current project state
├── config.json                    # Workflow configuration
├── research/                      # Research outputs from phases
├── [phase-number]/                # Per-phase directory
│   ├── PLAN.md                    # Executable task plan
│   ├── SUMMARY.md                 # What was implemented
│   ├── VERIFICATION.md            # Goal achievement verification
│   └── [research files]
└── codebase/                      # Codebase analysis documents
    ├── ARCHITECTURE.md            # Architecture analysis
    ├── STRUCTURE.md               # File structure guidance
    ├── STACK.md                   # Technology stack
    ├── INTEGRATIONS.md            # External integrations
    ├── CONVENTIONS.md             # Coding conventions
    ├── TESTING.md                 # Testing patterns
    └── CONCERNS.md                # Technical debt & issues
```

## Directory Purposes

**`agents/`:**
- Purpose: Agent prompt definitions (role, tools, methodology, process)
- Contains: 11 markdown files, one per specialized agent
- Key files:
  - `gsd-codebase-mapper.md` (16KB) — maps codebase for tech/arch/quality/concerns focus
  - `gsd-executor.md` (17KB) — executes plans with atomic commits + checkpoints
  - `gsd-planner.md` (38KB) — creates phase task plans with goal-backward thinking
  - `gsd-verifier.md` (16KB) — verifies goal achievement via gap analysis

**`commands/gsd/`:**
- Purpose: User CLI entry points (`/gsd:` slash commands)
- Contains: 32+ command definitions with argument hints and routing
- Key files:
  - `new-project.md` — initialize new project
  - `plan-phase.md` — create phase plan with optional research
  - `execute-phase.md` — run phase with wave parallelization
  - `research-phase.md` — deep research on phase technology
  - `map-codebase.md` — analyze codebase (tech/arch/quality/concerns)

**`get-shit-done/bin/`:**
- Purpose: Core tooling for GSD system
- Key file: `gsd-tools.cjs` — CLI tool for init, state, roadmap queries
- Sub-library (`lib/`):
  - `core.cjs` — Model profiles (quality/balanced/budget), output formatting
  - `state.cjs` — STATE.md read/write with locking
  - `phase.cjs` — Phase lifecycle queries
  - `config.cjs` — Configuration loading with defaults

**`get-shit-done/workflows/`:**
- Purpose: Multi-agent orchestration procedural steps
- Contains: 27 workflow definitions
- Key workflows:
  - `new-project.md` — Questions → Research → Requirements → Roadmap
  - `plan-phase.md` — Research (optional) → Plan → Verify (iteration)
  - `execute-phase.md` — Dependency analysis → Wave-based subagent execution
  - `verify-work.md` — Goal verification + gap closure planning

**`get-shit-done/references/`:**
- Purpose: Decision frameworks and procedural guides
- Key references:
  - `questioning.md` — Questions to scope projects
  - `model-profiles.md` — When to use Opus/Sonnet/Haiku per agent
  - `git-integration.md` — Git commit strategies and hooks
  - `ui-brand.md` — Output formatting consistency

**`get-shit-done/templates/`:**
- Purpose: Document and code templates for all GSD outputs
- Structure:
  - `codebase/` — Analysis templates (ARCHITECTURE.md, TESTING.md, etc.)
  - `project.md`, `requirements.md` — Initialization templates
  - `phase-prompt.md` — Context for phase execution
  - `continue-here.md` — Checkpoint recovery template

**`skills/`:**
- Purpose: Reusable conventions and patterns for projects
- Discovery: Each skill has SKILL.md describing when/how to use it
- Skills provided:
  - `orchestration/` — Delegation pattern for multi-commit work
  - `commit-workflow/` — Git commit message conventions
  - `just/` — Command runner configuration with examples
  - `testing-with-docker/` — E2E testing protocol

**`.planning/`:**
- Purpose: Project state and analysis (created by /gsd:new-project)
- Immutable: PROJECT.md (vision, scope)
- Evolving: STATE.md (current phase, blockers, completion dates)
- Per-phase: `.planning/[N]/` contains PLAN.md, SUMMARY.md, VERIFICATION.md
- Analysis: `.planning/codebase/` contains ARCHITECTURE.md, TESTING.md, etc. (written by gsd-codebase-mapper)

## Key File Locations

**Entry Points:**
- `.claude/commands/gsd/new-project.md` — Start new project
- `.claude/commands/gsd/plan-phase.md` — Start phase planning
- `.claude/commands/gsd/execute-phase.md` — Start phase execution
- `.claude/hooks/gsd-check-update.js` — Session initialization hook

**Configuration:**
- `.claude/settings.json` — Session hooks (startup checks, status line)
- `.planning/config.json` — Workflow preferences (model profile, git strategy)
- `.planning/PROJECT.md` — Project scope and vision

**Core Logic:**
- `.claude/get-shit-done/bin/lib/core.cjs` — Model profiles, output formatting
- `.claude/get-shit-done/bin/lib/state.cjs` — STATE.md state machine
- `.claude/get-shit-done/bin/lib/phase.cjs` — Phase query operations
- `.claude/get-shit-done/workflows/new-project.md` — Project initialization orchestration
- `.claude/get-shit-done/workflows/plan-phase.md` — Phase planning orchestration
- `.claude/get-shit-done/workflows/execute-phase.md` — Phase execution orchestration

**Testing:**
- `.claude/skills/testing-with-docker/SKILL.md` — E2E testing pattern documentation
- No test files in GSD itself (it's a framework, not an application)

**Codebase Analysis Output:**
- `.planning/codebase/ARCHITECTURE.md` — System architecture (written by mapper)
- `.planning/codebase/STRUCTURE.md` — File structure guidance (written by mapper)
- `.planning/codebase/STACK.md` — Technology stack (written by mapper)
- `.planning/codebase/TESTING.md` — Testing patterns (written by mapper)
- `.planning/codebase/CONVENTIONS.md` — Coding conventions (written by mapper)
- `.planning/codebase/CONCERNS.md` — Technical debt (written by mapper)

## Naming Conventions

**Files:**
- Agent definitions: `gsd-[agent-name].md` (kebab-case, all lowercase)
- Commands: `[command-name].md` (kebab-case matching `/gsd:command-name`)
- Workflows: `[workflow-name].md` (kebab-case)
- Templates: Descriptive names (lowercase + hyphens) or UPPERCASE.md for output docs
- State files: UPPERCASE.md (PROJECT.md, ROADMAP.md, STATE.md, REQUIREMENTS.md)
- Phase output: `[N]-[document-type].md` (e.g., `1-PLAN.md`, `1-SUMMARY.md`)

**Directories:**
- Agent directory: `agents/` (plural)
- Command directory: `commands/gsd/` (nested under commands)
- Workflow directory: `workflows/` (plural)
- Phase state: `.planning/[1-9]/` (numeric directory)
- Analysis output: `.planning/codebase/` (camelCase)

**Frontmatter (in Markdown files):**
- Agent YAML: `name:`, `description:`, `tools:`, `color:`
- Command YAML: `name:`, `description:`, `argument-hint:`, `allowed-tools:`, `agent:`
- Plan YAML: `phase:`, `plan:`, `type:`, `autonomous:`, `wave:`, `depends_on:`, `must_haves:`
- State YAML: Top-level frontmatter per markdown file type

## Where to Add New Code

**New Agent (specialized task type):**
- File location: `.claude/agents/gsd-[agent-name].md`
- Structure:
  - Frontmatter: `name:`, `description:`, `tools:` (read, write, bash, etc.), `color:`
  - `<role>` section: What the agent does
  - `<process>` section: Steps to execute
  - Tool-specific sections: Reference material agents need
- Register in: `.claude/get-shit-done/bin/lib/core.cjs` MODEL_PROFILES (add model choices)

**New Command (user-facing `/gsd:` command):**
- File location: `.claude/commands/gsd/[command-name].md`
- Structure:
  - Frontmatter: `name:` (matches `/gsd:name`), `description:`, `allowed-tools:`, `agent:` (if spawning agent)
  - `<objective>` section: What happens
  - `<execution_context>` section: @ references to workflows/templates
  - `<process>` section: Execute workflow from references
- Routing: Command system automatically routes to workflow defined in `<execution_context>`

**New Workflow (multi-step orchestration):**
- File location: `.claude/get-shit-done/workflows/[workflow-name].md`
- Structure:
  - Steps numbered with decisions, subprocess calls, state updates
  - References to agents, commands, tools
  - Checkpoint definitions where user input needed
  - State mutation instructions (update STATE.md, ROADMAP.md, etc.)
- Register in: `.claude/commands/gsd/[command].md` via `<execution_context>`

**New Skill (reusable pattern):**
- Directory location: `.claude/skills/[skill-name]/`
- Structure:
  - `SKILL.md` — Lightweight index (130 lines max), describes when/how to use
  - `rules/` — Specific rule files agents read
  - `examples/` — Template/example files
- Discovery: Planner/Executor reads `SKILL.md` from `.claude/skills/*/` directory
- Loading: Agent loads specific `rules/*.md` as needed, not full AGENTS.md

**New Codebase Analysis Document:**
- File location: `.planning/codebase/[ANALYSIS].md`
- When created: By `gsd-codebase-mapper` agent with `focus:` parameter
- Focus areas:
  - `tech` → writes STACK.md and INTEGRATIONS.md
  - `arch` → writes ARCHITECTURE.md and STRUCTURE.md
  - `quality` → writes CONVENTIONS.md and TESTING.md
  - `concerns` → writes CONCERNS.md
- Template: Use template from `.claude/get-shit-done/templates/codebase/[document].md`

**New Project Template (documentation):**
- File location: `.claude/get-shit-done/templates/[purpose].md`
- Naming: Descriptive names for procedural docs, UPPERCASE.md for document outputs
- Usage: Referenced by commands via `@./get-shit-done/templates/[name].md`
- Examples: `project.md` (PROJECT.md template), `roadmap.md` (ROADMAP.md template)

## Special Directories

**`.planning/research/`:**
- Purpose: Research output from domain/phase researchers
- Generated: Created by `gsd-project-researcher` and `gsd-phase-researcher`
- Committed: Yes (part of project knowledge)
- Structure:
  - `[phase]-RESEARCH.md` — Phase-specific research
  - `SUMMARY.md` — Overall recommendations
  - `STACK.md`, `FEATURES.md`, `ARCHITECTURE.md` — Detailed findings

**`.planning/[phase-number]/`:**
- Purpose: All outputs from a single phase execution
- Generated: Created at phase planning/execution
- Committed: Yes (essential for verification and resumption)
- Structure:
  - `1-PLAN.md` — Initial plan with tasks
  - `1-SUMMARY.md` — What executor implemented
  - `1-VERIFICATION.md` — Goal-backward verification results
  - `1-PLAN-revised.md` — If plan-checker requested revisions
  - Research files if phase was researched

**`.claude/get-shit-done/bin/lib/`:**
- Purpose: Shared utilities for GSD CLI tools
- Generated: No (checked into source)
- Committed: Yes (essential for GSD operation)
- Stability: Stable interface (breaking changes require version bump)

---

*Structure analysis: 2026-02-24*
