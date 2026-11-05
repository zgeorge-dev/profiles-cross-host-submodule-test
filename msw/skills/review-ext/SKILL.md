---
name: review-ext
description: A public test skill for verifying profile sync of symlinked and submodule-backed content.
---

# Review Ext

Fixture marker: `PUBLIC_REVIEW_EXT_V1`

This is synthetic, non-confidential test content. It requires no tools or
network requests and contains no private project source.

When asked to review an example:

1. Read only the sample text or code provided by the user.
2. Identify clear readability or correctness concerns.
3. Suggest small, concrete improvements.
4. State when no issues are found.

This skill's repository path is `msw/skills/review-ext/SKILL.md`. A parent
repository can link to this directory after checking out this repository as a
Git submodule. Changing this repository does not update a parent's pinned
submodule commit automatically.
