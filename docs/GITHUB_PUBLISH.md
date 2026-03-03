# Publish to GitHub

## 1. Initialize repository

```bash
cd /root/.codex/openclaw-oc101-ops
git init
git add .
git commit -m "feat: initial openclaw oc101 ops toolkit"
```

## 2. Create remote repository

Create an empty GitHub repo, then:

```bash
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## 3. Pre-push checklist

- No real secrets in `examples/`.
- No local `.env` tracked.
- No host-specific private data in docs.
- Scripts execute on a clean machine.
