---
name: grill-architecture
description: "Grill a plan or change with architecture in the design tree: premise, placement, reuse, seams and alternative shapes, recorded as ADRs. Use when designing a feature, a change, or a new project before a spec."
license: MIT
---

Call the Skill tool for "grilling", "domain-modeling" and "codebase-design". Run the session as grilling describes; this skill adds architecture branches to the design tree and a rule for consultations.

Those three skills come from `mattpocock/skills`. If any is missing, stop and give the user the install command: `bunx skills add mattpocock/skills --skill grilling --skill domain-modeling --skill codebase-design`.

## Before the first round

Explore the code and ADRs the idea touches with a sub-agent, or several if the codebase is large or the idea is complex. If a grilling session is already under way, add the branches to its current tree.

## Architecture branches

Each branch is a question with a recommended answer grounded in that exploration.

1. **Premise**: what the user's question or plan takes for granted: a second implementation, a migration, a named pattern. Check each against the ADRs and the code. A premise that fails becomes the next round's first question, ahead of any pattern.
2. **Placement**: the existing module that owns the change. A new module passes the deletion test.
3. **Reuse**: code that already does part of the work, named by file and symbol. "Nothing" is a search result: state what was searched.
4. **Seams**: count today's adapters behind each proposed seam. Two or more make it real. One makes it hypothetical: record it as such and name the event that would bring the second.
5. **Shape**: when the structure is the decision, present two or three alternatives, one without the new abstraction, each with a mermaid diagram and its cost. Use DESIGN-IT-TWICE when a new interface is the decision.
6. **Smallest version**: the least that delivers the outcome, and what the full version adds.

## Consultations

When a review by another model or a sub-agent / delegate returns, quote verbatim every finding that challenges a premise or a settled decision, and put each one to the user as a question in the next round. Summarise the rest.

## Done

Every architecture branch is settled by the user, and each settled decision lives in an ADR, so `to-spec` and later reviews inherit it.
