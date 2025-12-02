# Git Subtree Bidirectional Sync Guide

## Overview

This repository uses **git subtrees** for bidirectional synchronization with individual project repositories. This allows working on projects both within the integrated portfolio and independently in their standalone repos.

## Current Setup (Phase 1)

### Subtrees Configured
- ✅ **ai-land** ↔ https://github.com/vn6295337/ai-land.git

### Pending (Phase 2 & 3)
- ⏳ **ai-models-discoverer_v3** ↔ https://github.com/vn6295337/ai-models-discoverer_v3.git
- ⏳ **askme_v2** ↔ https://github.com/vn6295337/askme_v2.git

## Manual Sync Commands

### Push Changes (Portfolio → Individual Repo)
```bash
# Push ai-land changes to its GitHub repo
git subtree push --prefix=ai-land ai-land main
```

### Pull Changes (Individual Repo → Portfolio)
```bash
# Pull ai-land changes from its GitHub repo
git subtree pull --prefix=ai-land ai-land main --squash
```

## Automated Sync (GitHub Actions)

Two workflows provide automatic bidirectional sync:

### 1. Push Sync (`subtree-push.yml`)
- **Triggers:** On push to main with changes in `ai-land/**`
- **Action:** Automatically pushes ai-land changes to https://github.com/vn6295337/ai-land.git

### 2. Pull Sync (`subtree-pull.yml`)
- **Triggers:** Every 30 minutes (scheduled) or manual workflow dispatch
- **Action:** Automatically pulls ai-land changes from its GitHub repo

**Note:** Workflows are created locally but require manual push due to GitHub OAuth scope limitations. See deployment instructions below.

## Deploying GitHub Actions Workflows

The workflow files exist in `.github/workflows/` but need to be pushed manually:

**Option 1: GitHub CLI**
```bash
gh auth login --scopes workflow
git push origin main
```

**Option 2: Manual Git Push**
```bash
git push origin main
# Authenticate with your GitHub credentials when prompted
```

**Option 3: GitHub Web Interface**
1. Go to https://github.com/vn6295337/ai_portfolio_v2
2. Navigate to Actions → New workflow
3. Copy content from `.github/workflows/subtree-push.yml` and `subtree-pull.yml`

## Git Remotes

Current remotes:
```
origin      → https://github.com/vn6295337/ai_portfolio_v2.git (main portfolio)
ai-land     → https://github.com/vn6295337/ai-land.git (subtree)
ai-models   → https://github.com/vn6295337/ai-models-discoverer_v3.git (future)
askme       → https://github.com/vn6295337/askme_v2.git (future)
```

## Conflict Resolution

If sync conflicts occur:
```bash
# Pull with conflict
git subtree pull --prefix=ai-land ai-land main --squash

# Resolve conflicts manually in ai-land/ directory
# Edit conflicted files, keeping desired changes

# Complete the merge
git add ai-land/
git commit -m "Resolve sync conflict in ai-land"

# Push resolved version back
git subtree push --prefix=ai-land ai-land main
```

## Rollback

If subtree conversion causes issues:
```bash
# Return to backup branch
git checkout backup-pre-subtree
git branch -D main
git checkout -b main
git push origin main --force  # Use with caution!
```

## Phased Rollout Status

- ✅ **Phase 1:** ai-land subtree configured
- ⏳ **Phase 2:** Convert ai-models-discoverer_v3 to subtree
- ⏳ **Phase 3:** Convert askme_v2 to subtree

## Testing Bidirectional Sync

### Test Portfolio → ai-land
```bash
# Make change in portfolio
echo "test sync" >> ai-land/test-sync.txt
git add ai-land/test-sync.txt
git commit -m "Test: portfolio to ai-land sync"
git subtree push --prefix=ai-land ai-land main

# Verify in ai-land repo
cd /tmp
git clone https://github.com/vn6295337/ai-land.git test-ai-land
cd test-ai-land
cat test-sync.txt  # Should show "test sync"
```

### Test ai-land → Portfolio
```bash
# Make change in ai-land repo
cd /tmp/test-ai-land
echo "test reverse sync" >> test-reverse.txt
git add test-reverse.txt
git commit -m "Test: ai-land to portfolio sync"
git push

# Pull in portfolio
cd /home/vn6295337/ai_portfolio_v2
git subtree pull --prefix=ai-land ai-land main --squash
cat ai-land/test-reverse.txt  # Should show "test reverse sync"
```

## Production Validation

Before declaring Phase 1 complete:

- [ ] Push workflow files to GitHub
- [ ] Trigger subtree-push workflow manually
- [ ] Trigger subtree-pull workflow manually
- [ ] Make a test change in ai_portfolio_v2/ai-land and verify it syncs
- [ ] Make a test change in ai-land repo and verify it syncs back
- [ ] Verify ai-land production deployment still works (GitHub Pages/Vercel)
- [ ] Monitor for 7 days to ensure stability

## Support

For issues or questions about subtree sync:
1. Check git subtree documentation: `git subtree --help`
2. Review GitHub Actions workflow logs
3. Consult this guide's conflict resolution section
