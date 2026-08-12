---
name: Prefer low-friction launchers for tools the user runs repeatedly
description: When building personal tools, default to double-clickable launchers (.command on macOS) over terminal commands.
type: feedback
originSessionId: 9f9b2939-5573-4589-a8b5-8c3caa2e4019
---
When building local tools the user will run repeatedly, default to including a double-clickable launcher (`.command` file on macOS) alongside the terminal instructions, not just terminal commands.

**Why:** When I gave terminal commands to launch the dashboard, the user immediately asked "can you make it easy to launch like with just one click". They expect the polished UX path by default, not as a follow-up.

**How to apply:** For any local-only project that produces a runnable artifact (web server, REPL, daemon, etc.), include a `launch.command` (or platform equivalent) that handles port discovery, browser-open, and clean shutdown. For periodic tasks (data refresh, sync), include a separate `refresh.command` so the user doesn't have to remember CLI invocations.
