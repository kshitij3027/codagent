---
status: resolved
trigger: "When user asks the agent to remove files (rm -rf /tmp/test), the model asks clarifying questions instead of calling the shell tool, so the dangerous command detection (is_dangerous) and the [reason] approval line are never triggered."
created: 2026-02-25T10:00:00Z
updated: 2026-02-25T10:30:00Z
---

## Current Focus

hypothesis: CONFIRMED -- System prompt "ask for clarification before acting" instruction causes model to self-censor on destructive commands, bypassing the tool-level safety gate entirely.
test: Confirmed via code analysis and regex verification
expecting: N/A -- root cause found
next_action: Return diagnosis

## Symptoms

expected: Dangerous commands trigger explicit approval prompt with [reason] Dangerous command detected line
actual: Agent asked clarifying questions ("Delete recursively? Include hidden files?") instead of calling shell tool. The is_dangerous() function and approval gate were never invoked. Also slow response latency (>10s).
errors: None -- behavioral issue, not a code error
reproduction: Test 5 in UAT -- ask agent to "remove all files in /tmp/test"
started: Discovered during UAT

## Eliminated

- hypothesis: is_dangerous() regex does not match "rm -rf /tmp/test"
  evidence: Tested regex directly -- pattern `rm\s+(-\w*\s+)*-rf\s+[/~*]` matches "rm -rf /tmp/test" successfully. The detection code is correct.
  timestamp: 2026-02-25T10:03:00Z

- hypothesis: shell_tool() approval gate has a code bug
  evidence: Code in shell.py lines 151-159 is structurally correct -- if is_dangerous() returns True, it calls prompt_user_approval() with reason="Dangerous command detected". The bug is upstream (model never calls the tool).
  timestamp: 2026-02-25T10:03:00Z

## Evidence

- timestamp: 2026-02-25T10:01:00Z
  checked: System prompt in agent.py (lines 20-32)
  found: Prompt contains "If a request is ambiguous, ask for clarification before acting." -- this is a general instruction that the model applies to ANY request it considers unclear or risky, including destructive commands.
  implication: The model treats "remove all files in /tmp/test" as ambiguous and asks clarifying questions instead of calling the shell tool. This pre-empts the entire tool-level safety apparatus.

- timestamp: 2026-02-25T10:02:00Z
  checked: Safety architecture -- where is_dangerous() and approval gate live
  found: Both is_dangerous() and the "[reason] Dangerous command detected" approval prompt are inside shell_tool() (shell.py lines 142-172). They are ONLY invoked when the model calls the tool. There is no safety gate at the prompt or agent level.
  implication: The safety design assumes the model will always call the tool first. If the model decides not to call the tool (e.g., asks clarifying questions), the safety UX is entirely bypassed.

- timestamp: 2026-02-25T10:03:00Z
  checked: Dangerous pattern regex against "rm -rf /tmp/test"
  found: Pattern matches correctly. is_dangerous("rm -rf /tmp/test") returns True.
  implication: The detection code works. The problem is that the model never reaches it.

- timestamp: 2026-02-25T10:04:00Z
  checked: System prompt lacks any instruction about tool-level safety
  found: The system prompt does not tell the model that destructive commands have a built-in approval gate. The model has no way to know that its caution is counterproductive -- it thinks it IS the safety layer.
  implication: The model and the tool-level gate are both trying to be the safety layer, but the model's layer (asking clarifying questions) prevents the tool's layer (is_dangerous + approval prompt) from ever activating. They conflict rather than complement.

- timestamp: 2026-02-25T10:04:30Z
  checked: Tool docstring visible to model (agent.py lines 62-67)
  found: Tool description says "Execute a shell command. Returns stdout, stderr, and exit code." -- no mention of built-in safety, approval gate, or dangerous command detection.
  implication: Model has no information that the tool has safety guardrails. From the model's perspective, calling shell("rm -rf /tmp/test") would execute immediately with no safety net, so it errs on the side of caution.

## Resolution

root_cause: |
  The system prompt instruction "If a request is ambiguous, ask for clarification before acting" (agent.py line 27) causes the LLM to self-censor on destructive commands. The model interprets "rm -rf" requests as ambiguous/risky and asks clarifying questions instead of calling the shell tool. Since the dangerous command detection (is_dangerous()) and the "[reason] Dangerous command detected" approval gate both live INSIDE the shell_tool() function, they are never invoked.

  This is a prompt-safety architecture mismatch: the system prompt's ambiguity instruction and the model's inherent RLHF caution about destructive operations create a pre-tool safety layer that conflicts with and bypasses the intended tool-level safety layer. The model doesn't know the tool has a built-in approval gate, so it acts as its own safety layer.

  Contributing factors:
  1. System prompt says "ask for clarification before acting" with no exception for commands that have tool-level safety.
  2. System prompt does not inform the model that the shell tool has a built-in dangerous-command approval gate.
  3. Tool docstring makes no mention of safety guardrails, so model assumes calling it = immediate execution.
  4. LLMs (especially RLHF-trained) have inherent caution about destructive operations beyond what any system prompt says.
fix:
verification:
files_changed: []
