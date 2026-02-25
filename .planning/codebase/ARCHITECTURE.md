# Architecture

**Analysis Date:** 2026-02-24

## Pattern Overview

**Overall:** Multi-agent orchestration with command-driven workflow routing

**Key Characteristics:**
- Agent-per-responsibility pattern with specialized tool access
- Command interface (`.claude/commands/gsd/`) routes to orchestrator agents
- Orchestrator → Subagent delegation (context efficiency)
- Goal-backward verification methodology
- State machine managed via `STATE.md`, `ROADMAP.md`, `PROJECT.md`
- Extensible via Skills system (`.claude/skills/`)

## Layers

**Command Layer:**
- Purpose: CLI interface for user-facing workflows
- Location: `.claude/commands/gsd/`
- Contains: Command definitions with argument parsing, orchestrator routing
- Depends on: Agent system, GSD bin tools
- Used by: User via `/gsd:` commands (e.g., `/gsd:new-project`, `/gsd:plan-phase`)

**Orchestrator Layer:**
- Purpose: Parse input, delegate work, collect results, handle state
- Location: Not a single location — orchestrators are defined as command execution contexts
- Contains: Workflow routing logic defined in `.claude/get-shit-done/workflows/`
- Depends on: Agent prompts, GSD tools, internal state
- Used by: Command layer routes to workflows

**Agent Layer:**
- Purpose: Specialized task execution (research, planning, execution, verification)
- Location: `.claude/agents/`
- Contains: Agent prompt definitions (role, methodology, tool access, process steps)
- Agents:
  - `gsd-project-researcher.md` — Research domain ecosystem before roadmap
  - `gsd-codebase-mapper.md` — Analyze codebase structure, conventions, concerns
  - `gsd-roadmapper.md` — Transform requirements into phase structure
  - `gsd-planner.md` — Create executable task plans from phase goals
  - `gsd-phase-researcher.md` — Deep research on phase-specific technologies
  - `gsd-plan-checker.md` — Verify plans will achieve phase goal (before execution)
  - `gsd-executor.md` — Execute plans atomically with per-task commits
  - `gsd-verifier.md` — Verify phase goal achievement (after execution)
  - `gsd-debugger.md` — Debug execution failures and trace issues
  - `gsd-integration-checker.md` — Verify external integrations functional
  - `gsd-research-synthesizer.md` — Aggregate research into recommendations

**Tool & Config Layer:**
- Purpose: Shared utilities, state management, model selection
- Location: `.claude/get-shit-done/bin/lib/`
- Contains:
  - `core.cjs` — Model profiles, output helpers, file utilities
  - `state.cjs` — STATE.md read/write, frontmatter parsing
  - `phase.cjs` — Phase queries and lifecycle
  - `roadmap.cjs` — Roadmap phase queries
  - `milestone.cjs` — Milestone state management
  - `commands.cjs` — Command argument parsing
  - `frontmatter.cjs` — YAML frontmatter extraction
  - `verify.cjs` — Verification result storage
  - `template.cjs` — Template file loading
  - `init.cjs` — Project initialization utilities

**Workflow Templates:**
- Purpose: Define procedural steps for multi-agent workflows
- Location: `.claude/get-shit-done/workflows/`
- Key workflows:
  - `new-project.md` — Questions → Research → Requirements → Roadmap initialization
  - `plan-phase.md` — Research (optional) → Plan → Verify iteration loop
  - `execute-phase.md` — Wave-based plan execution with checkpoints
  - `research-phase.md` — Phase-specific technology research
  - `verify-work.md` — Verification with gap closure
  - Other workflows manage state transitions, milestone completion, phase insertion

**Skills Extension Layer:**
- Purpose: Reusable patterns and conventions for projects
- Location: `.claude/skills/`
- Skill types:
  - `just/` — Command runner configuration
  - `commit-workflow/` — Git commit conventions
  - `orchestration/` — Delegation patterns
  - `testing-with-docker/` — E2E testing approaches
- Each skill provides: SKILL.md (index) + rules/*.md (specific patterns)

**Reference & Template Layer:**
- Purpose: Documentation, templates, decision frameworks
- Location: `.claude/get-shit-done/references/` and `templates/`
- References:
  - `model-profiles.md` — Model selection guidance
  - `questioning.md` — Project scoping questions
  - `ui-brand.md` — Output formatting consistency
  - `planning-config.md` — Configuration options
  - `git-integration.md` — Git workflow principles
  - `tdd.md` — Test-driven development guidance
- Templates:
  - `project.md`, `requirements.md`, `roadmap.md` — Project initialization
  - `milestone.md`, `phase-prompt.md` — Phase documentation
  - `codebase/*.md` — Analysis documents (ARCHITECTURE, TESTING, CONVENTIONS, etc.)
  - `debug-subagent-prompt.md` — Debugging protocol
  - `continue-here.md` — Checkpoint recovery

## Data Flow

**Project Initialization Flow:**

1. User runs `/gsd:new-project` (command)
2. Orchestrator (workflow: new-project.md) questions user
3. Spawns `gsd-project-researcher` → research files to `.planning/research/`
4. Spawns `gsd-roadmapper` → creates `ROADMAP.md` with phases + success criteria
5. Creates `.planning/STATE.md` (project memory)
6. State machine ready for phase execution

**Phase Execution Flow:**

1. User runs `/gsd:plan-phase N` (command)
2. Orchestrator (workflow: plan-phase.md) loads phase from ROADMAP
3. Optional: Spawns `gsd-phase-researcher` → phase-specific research
4. Spawns `gsd-planner` → creates PLAN.md with tasks
5. Spawns `gsd-plan-checker` → verifies plan achieves goal (goal-backward)
6. If checker fails: Planner revises and re-checks (iteration loop)
7. User runs `/gsd:execute-phase N` (command)
8. Orchestrator (workflow: execute-phase.md) loads plans, analyzes dependencies
9. Groups into execution waves (parallel when independent)
10. Spawns `gsd-executor` per plan → per-task atomic commits + SUMMARY.md
11. Spawns `gsd-verifier` → verifies goal achievement via goal-backward
12. If verification fails: Create gap closure plans, repeat execution
13. Phase complete, STATE.md updated

**State Management:**

- `.planning/PROJECT.md` — Immutable project vision, scope
- `.planning/REQUIREMENTS.md` — Feature requirements with phase mapping
- `.planning/ROADMAP.md` — Phases with goals, success criteria, dependencies
- `.planning/STATE.md` — Current phase, milestones, completion dates
- `.planning/config.json` — Workflow preferences (model profile, git strategy, etc.)
- `.planning/[phase]/PLAN.md` — Executable task breakdown
- `.planning/[phase]/SUMMARY.md` — What executor implemented
- `.planning/[phase]/VERIFICATION.md` — What actually works + gaps

## Key Abstractions

**Phase:**
- Purpose: Delivery boundary with measurable goal and success criteria
- Identifier: 1-based number (Phase 1, 2, 3...)
- Structure: Goal (what users can do) + Success Criteria (observable behaviors) + Requirements
- Lifecycle: Unplanned → Planned → In Progress → Verified (or gaps, then re-execute)
- Examples: `ROADMAP.md` contains full phase definitions

**Plan:**
- Purpose: Executable breakdown of phase goal into 2-3 parallel tasks
- Structure: Frontmatter (phase, depends_on, wave) + objective + context + tasks (each with type, verification)
- Task types: code, test, config, docs, refactor, integration, research
- Verification: Each task has acceptance criteria (goal-backward from plan objective)
- Example location: `.planning/[phase]/[timestamp]-PLAN.md`

**Success Criteria (Goal-Backward):**
- Purpose: Observable behaviors proving phase goal achieved (not task completion)
- Format: "When this phase completes, users can X" (not "we implement X")
- Where defined: ROADMAP.md phase definitions
- How verified: `gsd-verifier` checks they exist and work in code (not just planned)

**Requirement:**
- Purpose: Feature or capability mapping to exactly one phase
- Format: "Users can X" (outcome-focused)
- Tracked in: REQUIREMENTS.md with phase column
- Validation: 100% coverage (no orphan requirements, no requirement in multiple phases)

**Checkpoint:**
- Purpose: Pause point during execution for human review
- Type: `type="checkpoint"` in PLAN.md tasks
- Behavior: Executor stops, returns result, waits for continuation
- Use case: Major architectural decisions, UI/UX reviews, integration tests

**Verification Gap:**
- Purpose: Observable behavior promised but not delivered
- Creation: `gsd-verifier` identifies in VERIFICATION.md gaps section
- Resolution: Gap closure plan created and executed iteratively
- Tracking: STATE.md milestone_blockers tracks active gaps

**Skill:**
- Purpose: Reusable convention set for projects
- Discovery: `.claude/skills/[skill-name]/SKILL.md`
- Structure: SKILL.md (index) + rules/*.md (specific patterns)
- Loading: Planner/Executor reads SKILL.md, loads specific rules as needed
- Example: `orchestration` skill defines delegation patterns used in all projects

## Entry Points

**User Command Interface (`/gsd:` commands):**
- Location: `.claude/commands/gsd/`
- Invocation: User types `/gsd:new-project`, `/gsd:plan-phase 1`, etc.
- Routing: Command definition executes workflow from `.claude/get-shit-done/workflows/`
- Examples:
  - `/gsd:new-project` → `new-project.md` workflow → spawns researchers/roadmapper
  - `/gsd:plan-phase 1` → `plan-phase.md` workflow → spawns planner/checker
  - `/gsd:execute-phase 1` → `execute-phase.md` workflow → spawns executors
  - `/gsd:verify-work 1` → `verify-work.md` workflow → spawns verifier

**Agent Spawning (from orchestrators):**
- Location: Workflows (in `.claude/get-shit-done/workflows/`) spawn agents
- Pattern: Orchestrator calls `Task` tool with agent name and prompt context
- Agent receives: `<files_to_read>` (mandatory), `<context>`, role definition
- Example: Planner spawned with phase goal, codebase docs, CONTEXT.md (user decisions)

**Tool Access Registration:**
- Location: `core.cjs` defines MODEL_PROFILES (which model + which tools)
- Pattern: Each agent has `tools:` list in frontmatter
- Enforcement: GSD system validates agent tool requests against profile
- Cost: Agent choice of tool has cost implications (e.g., gsd-codebase-mapper uses haiku to save tokens)

## Error Handling

**Strategy:** Goal-backward recovery with instrumented debugging

**Error Handling Patterns:**

1. **Execution Failure → Debugger Path:**
   - Executor catches task error (file write, bash command, etc.)
   - Executor creates SUMMARY.md with error details
   - User sees error, may run `/gsd:debug <phase>` to spawn `gsd-debugger`
   - Debugger analyzes failure trace, suggests fixes
   - Fixes applied as new gap closure plan

2. **Plan Verification Failure → Revision Loop:**
   - Plan-checker detects plan won't achieve goal
   - Plan-checker returns structured feedback with specific failures
   - Planner revises PLAN.md and resubmits to checker
   - Loop repeats until pass or max iterations

3. **Phase Verification Failure → Gap Closure:**
   - Verifier detects promised behavior missing or broken
   - Verifier documents gaps in VERIFICATION.md gaps section
   - User runs `/gsd:plan-phase N --gaps` to create closure plans
   - Executor runs gap plans separately, verifier re-checks
   - Iterate until all gaps resolved

4. **Project Initialization Error → Debug Command:**
   - Any workflow error (missing files, parsing errors, etc.)
   - Logs to stderr, returns failure message
   - User runs `/gsd:debug` without args to diagnose
   - Debugger checks project state, suggests recovery

**Instrumentation:**

- Executor records per-task timing, errors, commit SHAs in SUMMARY.md
- Verifier records per-criteria check results (pass/fail/partial) in VERIFICATION.md
- STATE.md tracks phase completion dates and current blockers
- All agents log substantial decisions to their output markdown

## Cross-Cutting Concerns

**Logging:**
- Framework: Structured via markdown output + error messages to stderr
- Pattern: Agents output findings to `.planning/[phase]/*.md` files
- Entry/exit: Each agent logs in frontmatter (`## Execution Summary` or similar)
- Search: Grep PLAN.md, SUMMARY.md, VERIFICATION.md for key decisions

**Validation:**
- Phase goals: Must have 2-5 success criteria (checked by roadmapper)
- Requirements: Must map 100% to phases (checked by roadmapper)
- Plans: Must address all success criteria (checked by plan-checker)
- Verification: Must test all success criteria exist + work (checked by verifier)
- Frontmatter: Must include wave/depends_on for parallel analysis (checked by execute-phase)

**Authentication:**
- Model selection: `core.cjs` MODEL_PROFILES per agent (quality/balanced/budget)
- Tool access: Each agent has explicit `tools:` list, enforced by system
- User context: CONTEXT.md (from `/gsd:discuss-phase`) locks decisions agents must honor
- Project context: `./CLAUDE.md` and `.claude/skills/*/SKILL.md` guide conventions

**Dependency Management:**
- Phase dependencies: Tracked in ROADMAP.md `depends_on:` field
- Plan dependencies: Tracked in PLAN.md frontmatter `depends_on:` field
- Task dependencies: Implicit in PLAN.md task order + wave assignment
- Parallel execution: Execute-phase analyzes dependency graph, groups into waves

---

*Architecture analysis: 2026-02-24*
