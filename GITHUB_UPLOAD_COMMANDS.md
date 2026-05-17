# GitHub Upload Commands

Run these from your main project folder.

```bash
git init
git add .
git commit -m "Add AI pharma manufacturing intelligence platform"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Important

Before pushing, make sure `.env` is not uploaded.

Check:

```bash
git status
```

If `.env` appears, remove it from Git tracking:

```bash
git rm --cached .env
```

Then commit again.

## Recommended Repository Name

```text
pharma-manufacturing-intelligence-platform
```
