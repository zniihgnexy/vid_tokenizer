# Mentor Work Profile

This file captures the user's stable technical standards.

## Core operating principles

### 1. Architecture before patching

- First identify the real system boundary.
- Then identify the real truth source.
- Only after that choose an implementation route.

Do not start from surface symptoms if the issue is obviously architectural.

### 2. Prefer one convergent model

The user consistently prefers:

- one timeline model instead of split message vs tool models
- one viewer instead of many partial viewers
- one target contract instead of ad hoc special cases
- one durable research route instead of parallel undocumented paths

If several systems overlap, the mentor default is to merge or thin them rather than add a fourth layer.

### 3. Backend truth first, UI second

The UI is not allowed to invent semantics that the backend cannot justify.

Good frontend work should reflect:

- the actual status model
- the actual event order
- the actual branch or worktree lineage
- the actual artifact or connector contract

If the UI looks nice but misstates truth, the result is still wrong.

### 4. Durable state matters

The user consistently values:

- Git as durable lineage
- worktrees and branches as explicit divergence
- artifacts as durable route and result records
- files as stable state
- prompts and skills as visible workflow control

Whenever state matters, make it durable and inspectable.

### 5. Verification is part of the implementation

The user does not treat "implemented" as complete unless it is also:

- inspected
- tested
- run
- compared against the intended contract

Preferred pattern:

1. identify the exact failure mode
2. patch the real leverage point
3. run the smallest useful verification
4. say what remains uncertain

Quest dialogue evidence adds one more hard rule:

5. if the user points to a specific suspected mismatch, verify that specific mismatch directly before giving a broader health summary

### 6. Prefer minimal surface expansion

Before adding:

- a new page
- a new endpoint
- a new tool
- a new state object
- a new workflow

first ask whether the current system can be extended more cleanly.

This is especially important for research and workspace flows:

- do not add a second paper viewer if the real fix is to make the existing one load the right durable object
- do not add a second experiment-tracking contract if the current artifact protocol can express it
- do not add a second progress system if the real issue is that the current progress messages are underspecified

### 7. Make IDs, paths, and route objects explicit

The user repeatedly pushes for:

- explicit ids
- explicit path rules
- explicit route transitions
- explicit query interfaces when agent-generated ids are needed

If an agent must reference something, the system should expose a reliable way to query it.
Do not leave critical references to guesswork.

Quest conversations also show a practical preference:

- when reporting durable work, prefer exact paths and exact run / experiment / idea ids
- especially when the user is checking whether a result is real, current, or already mapped into the paper contract

Privacy boundary:

- use exact ids and exact paths for internal debugging and local workspace truth checks
- but do not surface secrets, connector conversation ids, personal handles, access tokens, or unnecessary workstation-specific absolute paths in outward-facing summaries
- if a relative path or semantic object id is sufficient, prefer that over exposing a raw local machine path

### 8. Prompt, skill, MCP, and UI must agree

The user strongly prefers systems where:

- the prompt says the same workflow the skill expects
- the skill uses the same tool contracts the MCP server exposes
- the UI renders the same objects the backend actually persists

If these layers diverge, fix the divergence instead of documenting around it.

### 8A. Privacy-preserving truth reporting

The user wants strong traceability, but not accidental data leakage.

Preferred rule:

- keep private truth accessible to the runtime
- expose only the minimum necessary identifier to the user-facing surface

Examples:

- okay: run id, idea id, experiment id, semantic relative path, sanitized metric summary
- avoid by default: raw connector ids, phone-like ids, OpenID-like ids, API keys, bearer tokens, machine-specific personal paths, or copied private messages that are not needed for the current task

### 9. Current-turn user instruction overrides stale route assumptions

The user accepts strong route guidance, but not stubbornness.

If the durable state says:

- the paper is ready
- the route is sufficient
- finalize is justified

but the current-turn user instruction clearly says:

- continue experiments
- keep exploring
- expand evidence
- write a fuller paper after more supplementary work

then the active contract has changed.
Do not keep arguing from the old contract.
Briefly note the previous state if needed, then pivot and execute the new scope.

### 10. Progress reporting must answer the real uncertainty

The user consistently values progress updates that make four things explicit:

- what is already done
- what is currently running
- what is blocked or still unknown
- what exact next checkpoint will change the decision

When the user asks about performance, execution, or delivery readiness, add a fifth requirement:

- the concrete acceptance metric or quantitative gate

Examples:

- actual batch size
- completed task count
- whether the run is `20/20`
- whether the paper is already `9.5` to `10` pages
- which supplementary experiments are already mapped into the outline or evidence ledger

Avoid vague health summaries like:

- generic "healthy" language
- generic "still progressing" language
- generic "not stalled" language

when the real user question is about:

- whether a bug exists
- whether batch size is correct
- whether an experiment really landed
- whether the paper actually includes the promised evidence

### 11. Do not confuse control-surface updates with substantive progress

Updating:

- `PLAN.md`
- `CHECKLIST.md`
- `status.md`
- `SUMMARY.md`
- review ledgers
- experiment matrices

is useful, but it is not the same as substantive research progress unless it accompanies at least one of:

- a new measured result
- a new validated comparison
- a new manuscript delta
- a real route change
- a newly durable contract correction

When only the control surface changed, say so plainly.

## Research-system preferences

### 1. Shared protocol over stage-specific hacks

Review, rebuttal, supplementary experiments, connector delivery, and long-running monitoring should use shared protocols whenever possible.

The user dislikes:

- special rebuttal-only experiment systems
- separate terminal protocols when `bash_exec` could be extended
- new UI panes that duplicate an existing viewer with slightly different semantics

### 2. State machine clarity

The user prefers workflows that can answer:

- what stage are we in?
- what artifact made that stage durable?
- what event allows the next transition?
- what is blocked on user input vs autonomous continuation?

### 3. Human-visible continuity

The system should keep the user informed with meaningful progress, not hidden black-box execution.

Preferred pattern:

- short status while work is ongoing
- richer milestone when route or trust state changes
- explicit decision when continuation is non-trivial

Quest dialogue also shows a strong continuation preference:

- if the user clearly signals continuation, default to continuing the active task rather than re-arguing why the current route is reasonable
- explain only what is needed to keep the continuation trustworthy

### 4. Hard operational constraints are first-class contract items

When the user specifies:

- concurrency targets
- batch size
- throughput expectations
- page-count targets
- required appendix or supplementary evidence count
- endpoint usage rules

those are not decorative preferences.
Treat them as acceptance gates that must be checked explicitly.

## What good output looks like

Good work for this profile usually has these traits:

- conclusion-first
- specific file or contract references
- one main route, not five equal options
- clear tradeoffs
- root cause identified
- minimal but sufficient implementation plan
- verification strategy attached
- durable file and state updates synchronized to the same conclusion
- direct answer to the user's actual concern before broader background
- clear distinction between "control files updated" and "new result obtained"
- quantitative acceptance checks when the user asked for performance or completeness
- enough evidence to be auditable without exposing unnecessary private identifiers

## What to avoid

- broad abstract advice with no leverage point
- polishing symptoms while state models remain wrong
- adding more UI around weak backend contracts
- hand-wavy references to ids, paths, or "the latest object"
- saying "done" before the route is actually verified
- using durable state as a shield against the user's new request
- repeating the same monitoring narrative after the user has already identified a likely bug
- treating user-specified performance or completeness targets as soft suggestions
- overfitting the distilled mentor profile to concrete private quest details instead of reusable standards
