---
name: reference_readback_verification
description: Wrapped-CLI writes must be verified by read-back — never trust an exit code or a success message; success text can print while the write silently fails
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1d009b0a-f547-4527-a83f-e55459326c69
---

A wrapped CLI (a script fronting `bw`, `git`, an API) can print success while the underlying write silently fails. Exit 0 and a "✓ done" message are not proof. **Verify every write by reading it back** from the store you wrote to.

**Two real failures:**
- `secrets-push` printed "✓ Updated" while silently failing to write to Bitwarden for **8 days** — the wrapped `bw unlock` broke under a non-interactive TTY, so the push no-op'd but the wrapper reported success. Nobody caught it until a `secrets-pull` came back stale.
- `git push origin --delete $list` with a multi-line shell variable silently no-op'd at exit 0 — the variable didn't expand into per-branch args the way expected.

**How to apply:**
- After a wrapped write, read it back: `secrets-pull` and diff, `git ls-remote` for remote refs, re-query the API for the row you wrote. Confirm the value actually landed.
- Deleting remote branches: loop per-branch (`for b in $list; do git push origin --delete "$b"; done`), and verify with `git ls-remote` — **never** `git branch -r` (that reads the stale local cache, not the remote).
- Treat any wrapper's success message as a claim to check, not a fact. See [[reference_secrets_management]] for the secrets-push/pull mechanics.
