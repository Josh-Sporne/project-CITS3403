# AI Use Acknowledgement

This document discloses the team's use of generative AI tools during the development of Plate Theory, in line with UWA's academic integrity policy and the CITS3403 unit guidelines.

## Tools used

The team used **large language models** (Claude / ChatGPT / GitHub Copilot — adjust to whatever your team actually used) as collaborative coding assistants during development.

## What AI was used for

- **Code generation and refactoring** — AI assisted with writing form validators, route handlers, Jinja templates, JavaScript handlers, CSS rules, and test helpers. All AI-generated code was reviewed, tested, and adapted by team members before being committed.
- **Debugging assistance** — AI helped diagnose merge conflicts, SQLAlchemy errors, template rendering bugs, JavaScript silent failures, and API response shape mismatches.
- **Code review and audit** — AI was used to systematically check team members' workstreams for bugs, missing validators, accessibility issues, and inconsistencies (e.g. case-sensitivity bugs, missing input validation, untracked image fallback patterns).
- **Documentation** — AI suggested commit messages, pull-request descriptions, and the structure of this disclosure. Drafts were edited by team members before posting.
- **Brainstorming and architectural discussions** — AI was used as a sounding board for design choices (e.g. how to structure the `Tag` / `RecipeTag` schema, how to handle URL-vs-filename autodetection in image fallbacks, when to use Bootstrap modals vs native confirms).

## What AI was NOT used for

- **Writing the assignment specification or audit documents** — those came from the team and the unit's marking criteria.
- **Generating user content** — recipe data, descriptions, ingredient lists, and images were sourced manually or via free public APIs (Loremflickr food photos for placeholder images; Wikimedia Commons for curated recipe images, used under their respective licenses).
- **Writing this acknowledgement to misrepresent the use of AI** — every team member can explain the AI-assisted code they committed, and we did not submit AI-generated text as original creative writing.

## Quality assurance

All AI-suggested code was:

1. **Read and understood** by the team member who committed it.
2. **Tested locally** before being pushed.
3. **Reviewed in PRs** by other team members where applicable.
4. **Cited** in commit messages and PR descriptions where the AI's contribution was substantial (e.g. "AI-assisted refactor of validator").

## Contact

If markers have questions about which specific contributions were AI-assisted vs hand-written, the team is happy to discuss any commit, file, or PR in detail.
