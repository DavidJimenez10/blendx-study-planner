---
name: to-prd
description: Turn the current conversation context into a PRD and publish it to the project issue tracker. Use when user wants to create a PRD from the current context.
---

This skill takes the current conversation context and codebase understanding and produces a PRD. Do NOT interview the user — just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you — run `/setup-matt-pocock-skills` if not.

## Core Principles

### Lead with problem and context
Maggie Crowley: "The most important section is the first part - what is the background and context? What is the problem, why does it matter, and why does it matter now?" Center the team on the 'why' and the urgency before discussing solutions.

### The PR/FAQ forces clarity
Bill Carr: "Whenever we're devising a new product, we start by writing a press release describing it in a way that speaks to the customer. The idea better jump off the page." Use the PR to describe customer, problem, and solution in factual, data-rich language.

### Demos before memos in AI age
Aparna Chennapragada: "If you're not prototyping and building to see what you want to build, you're doing it wrong. Prompt sets are the new PRDs." For AI features, include functional prototypes and prompt sets as core requirements.

### Evals as living PRDs
Hamel Husain & Shreya Shankar: "This is the purest sense of what a product requirements document should be - this eval judge that's telling you exactly what it should be, and it's automatic and running constantly." Translate product requirements into executable evaluations for AI products.

### Keep it lightweight for action
Eric Simons: "We tend to keep them pretty light. I like to have the minimal amount of context that ensures everyone's on the same page and that key outcomes will be present when we get there." Focus on key outcomes rather than exhaustive details that developers ignore.

### PRDs demonstrate craft
Vikrama Dhiman: "Is your PRD quality good enough? Are you writing drafts that go to care teams, marketing teams? You must have impact through the artifacts you work on." High-quality PRDs demonstrate professional craft and create clarity at scale.

### AI can scaffold the basics
Claire Vo: "I had used ChatGPT to come up with a very serviceable PRD spec for this very technical product." Use AI to scaffold basics like user stories and out-of-scope items, then focus on high-level strategy and narrative.

### Live PRDs reduce ambiguity
Guillermo Rauch: "The product management team is now actually building the product. We've specced out in v0, think of it as a live PRD. The amount of detail - we're all saying 'just ship it.'" Interactive, animated prototypes reduce ambiguity and speed up approval.

### Include the 'Why Now'
Justify the timing of this investment against other opportunities. If you can't explain why this matters now versus later, the priority is questionable.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

3. Write the PRD using the template below, then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>

## Deep Dive

For all 14 insights from 11 guests, see `references/guest-insights.md`