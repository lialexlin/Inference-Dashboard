---
name: Explain via the browser, not file paths
description: When explaining how the dashboard works, point to what the user sees in the rendered site and open it in the browser — don't cite file paths or line numbers.
type: feedback
originSessionId: 3a822a77-b7ae-4acb-b7dd-54b183c5984b
---
When explaining where something lives or how something works on the Inference Dashboard, reference what the user sees in the running site ("the homepage layer cards", "the Bottleneck status panel on a layer page", "the type filter in the signals sidebar") and actually open the page in the browser to show it. Do not cite file paths like `layer.html:143` or `assets/components.js:30` in user-facing explanations.

**Why:** User is a retail investor, not a developer (see `user_personal_investor.md`). File paths are noise — they navigate the product through its UI, not its source. Saying "layer.html" is meaningless to them.

**How to apply:**
- For "where does X live / how does Y work" questions: navigate to the page in Chrome (claude-in-chrome or playwright tools), take a screenshot or describe by visible elements, and explain in those terms.
- File paths are still fine for *me* to use internally while investigating, and fine to mention when the user is explicitly asking about implementation, code changes, or files to edit.
- When making code changes, still reference files in the diff/PR — this rule is about *explanation*, not editing.
