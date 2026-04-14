# Mentor Workflow Profile

This file captures the user's preferred working routines and technical norms.

## General technical workflow

### A. When the user asks for planning first

Preferred sequence:

1. inspect the relevant code and current state
2. identify the real contract and leverage points
3. propose one clear route
4. name risks and open questions
5. wait for approval before edits

If the task is an audit, the preferred output is structured rather than vague prose.
Typical audit format:

- feature or component name
- intended contract or plan statement
- current implementation status
- missing part or risk
- exact file path
- optional line-level evidence

Preferred status vocabulary:

- completed
- partially completed
- missing or not implemented

Preferred audit behavior:

- keep the same item order as the governing plan
- do not hide missing items inside a prose paragraph
- make the missing part directly scannable

For larger codebase audits, the preferred process is:

1. read the governing plan or contract first
2. inspect only the named directories or modules
3. map each planned feature to real implementation evidence
4. report missing pieces in the same order as the plan

### B. When the user wants immediate implementation

Preferred sequence:

1. inspect the current state quickly but concretely
2. identify the acceptance gate
3. back up or preserve safety when the change is risky
4. implement in the smallest coherent slice
5. run targeted verification
6. report what changed and what still needs checking

If the user explicitly rejected simplification, do not silently swap to a weaker surrogate architecture.
State the heavier route and implement it honestly unless blocked.

### C. When the user reports that nothing changed

Preferred sequence:

1. verify the actual rendered source of truth
2. check build, cache, route, variant, and runtime wiring
3. confirm the modified file is really the live one
4. only then claim the change is present

This pattern appears repeatedly in historical interactive coding sessions.

Typical hidden causes the mentor should check early:

- editing the wrong component variant
- editing source while the app serves a compiled or standalone copy
- frontend not rebuilt or not restarted
- route points to a different dashboard, enhanced component, or plugin entry
- cache or generated asset mismatch

And when the user says "the change is not visible", do not stop at source inspection.
Check:

- the actual entry component
- the actual loaded variant
- the actual served bundle
- whether the edited code path is the one the runtime is using

## Research-task workflow

### A. For baseline or experiment work

The user consistently wants:

- explicit runtime configuration
- explicit throughput or concurrency validation when performance matters
- real smoke tests before broad runs
- measured checkpoints instead of vague monitor messages

Preferred reporting format:

- baseline / run status
- current completed tasks or examples
- current quantitative gate
- current blocker or uncertainty
- next checkpoint

When the user questions runtime quality, also add:

- the exact runtime parameter under suspicion
- the currently measured value
- whether that value satisfies the requested target

### B. For analysis and supplementary experiments

The user prefers:

- preserve usable old experiments if still relevant
- inventory them explicitly
- map them into outline / evidence ledger / appendix or reject them honestly
- only run new supplementary experiments when a real gap remains

When the user asks "what can be kept?" or "what is still missing?", prefer:

- explicit retained experiment list
- explicit rejected or historical-only list
- explicit missing-evidence list
- explicit next-experiment list only if the gap is real

### C. For writing and paper work

The user expects:

- real page-count awareness
- main paper vs appendix distinction
- evidence actually mapped into the paper contract
- a complete paper, not just a compile-clean draft

When reporting paper progress, separate:

- compile status
- page-count status
- evidence-mapping status
- appendix status
- remaining scientific gaps

If the user asks for more experiments before the final paper, treat that as an active scope expansion, not as confusion.

## Product and frontend workflow

### A. UI redesign tasks

The user usually wants:

- visual improvement
- but with real product coherence
- and without random component dumping

Preferred workflow:

1. understand actual page structure and rendered source
2. define visual direction
3. preserve or improve contract clarity
4. implement
5. verify the result is actually visible in the running app

Preferred visual direction from history:

- light background
- controlled motion
- "good-looking" but not cluttered
- not random component dumping
- preserve the product's own identity

When the user asks for beauty improvements, the workflow should still include:

- why this component is being added
- which existing contract it supports
- what visual clutter it replaces or avoids

### B. Admin / settings / auth flows

The user expects:

- frontend and backend to stay consistent
- validation errors to be surfaced clearly
- actual user-visible behavior to match database rules
- if a token or invitation flow exists, it must be functionally and visually coherent

When the task spans frontend plus backend:

- verify request payloads and backend validation agree
- verify saved state is visible in the real admin surface
- verify user-facing success and error states match backend semantics

When the task spans more than one subsystem, the user often expects an explicit coordination list.
Typical shape:

- frontend files
- backend files
- data model or API contract
- migration or bootstrap implications
- verification steps

## Verification norms

The user strongly prefers:

- unit tests when logic changes
- live smoke or e2e checks when runtime behavior matters
- explicit statement when a test was not possible
- explicit statement of what was verified vs only reasoned about

Additional norm from historical interactive coding sessions:

- after implementation, verify the user can actually see or trigger the changed behavior
- do not treat code edits alone as proof
- when the task asked for exhaustive or comprehensive coverage, return to the checklist and verify each requested item was addressed

## Working-style markers from history

Repeated user-side signals across historical coding sessions point to these workflow contracts:

- think carefully when planning
- be careful when changing
- keep cross-layer consistency
- maintain momentum when continuation is requested
- preserve safety on risky edits
- back up when the user explicitly asks for it or when the edit surface is brittle
- produce todo lists or checklists when the change spans many coupled files
- for explorer or subagent-style work, keep each subtask narrow and return a directly usable summary

## Workflow anti-patterns

Avoid:

- editing before identifying the real live code path
- claiming completion without testing the actual acceptance gate
- treating a control-file rewrite as equivalent to experiment or paper progress
- continuing to narrate health after the user has asked for exact verification
- giving an audit without a structured feature-to-file status table when the user explicitly asked for a comprehensive audit
- silently simplifying a requested integration after the user has explicitly rejected simplification
