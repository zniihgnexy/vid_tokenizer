# Mentor Taste Profile

This file captures the user's stable product and UI preferences.

## Product taste

### 1. Real systems should feel coherent

The user strongly prefers products that feel like one system, not many stitched demos.

Good signs:

- shared data contracts
- shared viewers
- shared interaction metaphors
- one obvious truth source
- one route to inspect the same object across surfaces

Bad signs:

- duplicate pages with slightly different semantics
- one-off dialogs that bypass the normal model
- multiple status models for the same run
- patch-specific UI that does not compose with the workspace

### 2. Explanatory power beats decoration

The product should help the user understand:

- where they are
- what is happening
- what changed
- what they can do next

Interfaces that look stylish but hide state or route are not aligned with this profile.

## UI taste

### Visual direction

Stable user preference:

- low saturation
- Morandi family palettes
- restrained contrast
- clear hierarchy
- minimal but intentional chrome

This does not mean "flat and boring".
It means the interface should feel composed rather than noisy.

### Layout

Preferred layout traits:

- obvious primary area
- clean secondary controls
- low duplication
- enough whitespace to read state
- tabs and dialogs that map to real objects

### Motion

Motion should:

- reveal status
- smooth transitions
- preserve continuity

Motion should not:

- distract
- simulate fake progress
- hide slow data paths
- force a new metaphor when the system already has one

### Surface-specific taste

#### Workspace and copilot

- timelines should preserve order and truth
- tool calls should feel inspectable, not magical
- inputs should make current mode obvious
- tabs should open real objects, not decorative placeholders
- progress surfaces should separate:
  - completed
  - running
  - blocked
  - next checkpoint
- user-facing updates should be concise but evidence-bearing, not generic reassurance
- user-facing detail should be inspectable without unnecessarily exposing private identifiers or secret-bearing payloads

#### Settings and flows

- use stepwise flows when the contract is sequential
- keep forms explicit
- explain why a setting exists, what it enables, and what risk it carries

#### Research canvases

- branch-centric or evidence-centric views are preferred over arbitrary node spam
- every visible node should map to something durable
- opening a node should expose the actual evidence chain
- if a paper or experiment is claimed complete, the UI should make it easy to inspect the actual supporting files, result records, and mapping into the outline or evidence ledger

## Taste anti-goals

Avoid:

- generic AI cards everywhere
- unrelated gradients and random color accents
- fake complexity
- too many nested frames
- long explanatory paragraphs in the interface
- a beautiful shell over a confused model
- a progress badge that hides the real blocker
- polished finality cues when the underlying route is still being contested by the user
- exposing raw secret or identity-bearing fields when a cleaner semantic label would suffice

## Fast checks

When judging a UI route, ask:

1. Does this expose the real object or invent a presentation-only object?
2. Does this make the user's next action clearer?
3. Does this reduce duplication?
4. Does the visual treatment support the underlying state?
5. Would this still make sense after the backend evolves?
