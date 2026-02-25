---
status: resolved
trigger: "When user rejects a shell command (types 'n' at approval prompt), the agent doesn't acknowledge the rejection. Instead, it offers to run the same command again."
created: 2026-02-25T10:00:00Z
updated: 2026-02-25T10:30:00Z
---

## Current Focus

hypothesis: CONFIRMED -- system prompt lacks rejection handling instructions
test: Traced full data flow from shell_tool rejection return through pydantic-ai agent.run() to model response
expecting: n/a (diagnosed)
next_action: Return diagnosis

## Symptoms

expected: On command rejection (typing n), agent acknowledges rejection and asks what user wants to do instead
actual: Agent ignores the rejection message and offers to re-run the same command. Example: user asked to print first 10 lines of README.md, typed 'n' at approval, agent responded "I can run head -n 10 README.md to print the first 10 lines here. Would you like me to run it now?"
errors: None -- no crash, just wrong behavioral response
reproduction: Test 4 in UAT -- type any command request, reject with 'n' at approval prompt
started: Discovered during UAT

## Eliminated

- hypothesis: Rejection message is lost/dropped before reaching the model
  evidence: Traced data flow -- shell_tool returns rejection string, shell wrapper in agent.py passes it through directly, pydantic-ai agent.run() handles full ReAct loop internally so tool result IS sent back to model. No transformation or loss anywhere in the chain.
  timestamp: 2026-02-25T10:02:00Z

- hypothesis: Code bug in the approval gate logic (wrong return value, logic error)
  evidence: shell.py lines 163-169 correctly check `if not approved` and return clear rejection string. prompt_user_approval correctly returns False when input is 'n'. No code-level bug.
  timestamp: 2026-02-25T10:02:00Z

## Evidence

- timestamp: 2026-02-25T10:01:00Z
  checked: shell.py shell_tool() rejection return value (lines 165-169)
  found: Returns "Command rejected by user. The user chose not to run this command. Ask the user what they'd like to do instead." -- message is clear and well-crafted
  implication: The tool does its job correctly

- timestamp: 2026-02-25T10:01:30Z
  checked: agent.py shell wrapper (line 68) and run_agent_turn (lines 98-100)
  found: Wrapper does `return await shell_tool(command)` -- direct passthrough. run_agent_turn uses `agent.run()` which handles the full ReAct loop internally (model calls tool, receives result, generates response). No interception or transformation.
  implication: Rejection message reaches the model as a tool result without any loss

- timestamp: 2026-02-25T10:02:00Z
  checked: agent.py SYSTEM_PROMPT (lines 20-32)
  found: System prompt covers conciseness, clarification, error handling (non-zero exit codes), multi-step summaries. Contains ZERO instructions about handling command rejections or respecting user approval decisions.
  implication: Model has no guidance on what to do when a tool call is rejected by the user

- timestamp: 2026-02-25T10:03:00Z
  checked: The relationship between tool-result instructions and system-prompt instructions
  found: The rejection message includes "Ask the user what they'd like to do instead" -- this is an instruction embedded in a tool return value. Without corresponding system prompt authority, the model's trained helpfulness causes it to prioritize task completion over the tool-embedded instruction. The model interprets the unfulfilled task as the primary goal and re-offers the command.
  implication: Tool-level instructions are insufficient without system-prompt-level reinforcement for behavioral changes

## Resolution

root_cause: The system prompt in agent.py (SYSTEM_PROMPT, lines 20-32) has no instructions for handling user command rejections. When the shell tool returns a rejection message, the model receives it but has no system-level guidance to respect it. The model's default "helpful" behavior causes it to re-offer the same command instead of acknowledging the rejection and asking what the user wants. The rejection message embedded in the tool return value ("Ask the user what they'd like to do instead") is not authoritative enough on its own without system prompt backing.
fix:
verification:
files_changed: []
