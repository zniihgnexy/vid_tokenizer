# Mentor Correction Rules

Use this file when the work is drifting.

## Common failure smells

### 1. Patchwork instead of convergence

Smell:

- many local fixes
- several near-duplicate viewers or routes
- special cases added faster than contracts are cleaned up

Correction:

- identify the shared object
- identify the shared contract
- collapse duplicate routes before adding more polish

### 2. Surface polish over truth

Smell:

- nice UI but wrong status model
- clean layout but fake progress
- good copy but unverifiable behavior

Correction:

- fix backend truth and event semantics first
- then re-check the UI

### 3. Long planning without leverage

Smell:

- many pages of analysis
- no exact files or contracts
- no verification route

Correction:

- reduce to one main bottleneck
- state exact leverage points
- attach one concrete verification step

### 4. Generic AI output

Smell:

- too many equal options
- bland product direction
- language that sounds correct but not specific
- advice that could fit any codebase

Correction:

- make the answer repository-shaped
- name the contract, path, model, or route
- prefer one clear recommendation when the evidence supports it

### 5. Repeated retries on the same failed path

Smell:

- the system keeps doing the same thing with different wording
- no new diagnostic information is gathered

Correction:

- stop the retry loop
- inspect the real state
- change the approach, not just the phrasing

### 5A. Monitoring optimism instead of bug verification

Smell:

- the user points to a concrete mismatch
- the system answers with "still healthy", "still progressing", or "not stalled"
- the same reassurance is repeated across multiple turns

Correction:

- treat the user's suspicion as the active debugging target
- verify the exact claimed mismatch directly
- only return to broader health reporting after that specific claim is checked

### 5C. Control-surface progress inflation

Smell:

- the answer reports many updated files
- but no new measurement, comparison, or manuscript delta exists
- the wording still implies major forward progress

Correction:

- explicitly separate bookkeeping progress from substantive progress
- say what changed in the control surface
- say what did not change in the underlying result state
- state the next real acceptance checkpoint

### 5B. Defending stale closure against a new instruction

Smell:

- durable state says a line is done
- the user explicitly asks to continue exploration, add experiments, or rewrite a fuller paper
- the system keeps arguing from the old closeout state

Correction:

- note the previous closure state briefly
- switch the active contract to the new user instruction
- translate the new request into the smallest honest continuation route

### 6. Prompt / skill / tool disagreement

Smell:

- prompt says one workflow
- skill says another
- tool surface cannot actually support either one

Correction:

- choose the real protocol
- rewrite the weaker layers to match it
- do not document around the mismatch

### 7. IDs, paths, or references left implicit

Smell:

- "latest"
- "current item"
- "that run"
- "the selected branch"

without a reliable query mechanism

Correction:

- make the reference explicit
- or add the query surface the agent needs

### 8. Durable references used as a shield

Smell:

- the answer names many files, reports, and summaries
- but still does not answer the user's real question

Correction:

- use durable references as evidence, not as evasion
- first answer the actual question
- then cite the files that justify that answer

### 8A. Private details copied into the distilled style

Smell:

- the profile or reply includes raw connector ids
- copied user handles or message ids appear where a semantic label would work
- secrets, tokens, or machine-specific personal paths leak into summaries

Correction:

- remove the private literal
- keep only the reusable rule or sanitized evidence
- use relative paths, stable semantic ids, or generic labels unless the raw value is strictly necessary

### 9. User continuation intent ignored

Smell:

- the user repeatedly says "继续"
- the answer keeps re-explaining why the current route is already enough
- forward motion stalls

Correction:

- interpret "继续" as permission to push the active route forward
- if a blocker exists, state the blocker and the smallest next action
- otherwise stop defending and continue execution

### 10. Acceptance gate left implicit

Smell:

- the user gave a hard target like batch size, throughput, page count, or experiment count
- the answer talks generally about progress
- the target itself is never checked

Correction:

- promote the user-specified target into an explicit acceptance gate
- report the current measured value against that gate
- if it is unknown, say it is unknown and verify it next

## Preferred correction pattern

1. name the real smell
2. explain why it matters
3. identify the smallest convergent fix
4. say what not to change
5. hand back to the primary skill
