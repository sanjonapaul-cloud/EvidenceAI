# Team Development Guide (Git and GitHub)

For six beginners sharing one repository. Keep it simple and consistent.

## 1. One-time setup

```powershell
git clone <repo-url> EvidenceAI
cd EvidenceAI
git config user.name "Your Name"
git config user.email "you@example.com"
```
Member 6 creates the repository, adds everyone as collaborators, and enables **branch protection on `main`** (require a pull request and one approval; no direct pushes).

## 2. Branches

- `main` — always working and demo-ready. Nobody commits to it directly.
- Work branches, one per task, named `area/short-description`:
  `frontend/citation-card`, `backend/delete-endpoint`, `pdf/header-cleanup`, `rag/tune-threshold`, `citations/semantic-check`, `integration/ci-fix`.

```powershell
git checkout main
git pull
git checkout -b pdf/header-cleanup
```

## 3. Commits

Small, frequent, with a clear message in the imperative mood:
```
pdf: remove repeated page headers during cleaning
```
Prefix with your area (`frontend:`, `backend:`, `pdf:`, `rag:`, `citations:`, `docs:`, `ci:`). One idea per commit.
```powershell
git status
git add server/app/document_processing/cleaner.py server/tests/test_chunking.py
git commit -m "pdf: remove repeated page headers during cleaning"
```
**Never commit:** `.env`, API keys, `node_modules/`, `.venv/`, `server/data/`, your own PDFs. Check `git status` before every commit. If a secret is ever committed, tell Member 6 immediately and **revoke the key** (deleting the commit is not enough).

## 4. Keep your branch current

```powershell
git fetch origin
git merge origin/main        # resolve conflicts if any, run the tests, commit
```
Do this at least daily and before opening a pull request.

## 5. Pull requests

1. Push: `git push -u origin pdf/header-cleanup`
2. Open a PR on GitHub into `main`. Fill in the template (what changed, how you tested it, screenshots for UI).
3. Keep PRs small (ideally under ~300 changed lines).
4. Run before requesting review: `python -m pytest` (server) and `npm run build` (client, if you touched it).

## 6. Reviews

- Every PR needs **one approval** from the **owner of the files changed** (see `team_responsibilities.md`); Member 6 reviews anything touching shared files.
- Review within one working day. Check: does it run? tests added? API docs updated? no secrets? readable for a beginner?
- Be kind and specific: "Could we rename `x` to `chunk_text`?" beats "unclear".
- The author fixes comments and re-requests review; the **reviewer does not push to the author's branch** without asking.
- Merge with **Squash and merge**, then delete the branch.

## 6b. Conflicts

If Git reports a conflict, open the file, keep the correct lines, remove the `<<<<<<<`, `=======`, `>>>>>>>` markers, run the tests, then `git add` and `git commit`. If unsure, ask the other file owner — do not guess.

## 7. Integration routine

- **Member 6** checks `main` after each merge: backend tests, frontend build, quick manual run of the demo script.
- Contract changes (API, chunk metadata, citation format) go in **one PR** that updates code, tests and docs together, and is announced in the team chat.
- **Demo freeze:** 24 hours before a demo only bug-fix PRs are merged. Tag the demo version: `git tag demo-1 && git push --tags`.

## 8. Weekly rhythm (suggested)

Mon: pick tasks (GitHub Issues, labelled by area) · Daily: 10-minute stand-up (done / next / blocked) · Fri: merge, integration test, update `docs/testing_guide.md`.
