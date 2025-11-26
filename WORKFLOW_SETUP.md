# GitHub Actions Workflow Setup Guide

## Issue

The subtree sync workflows need a **Personal Access Token (PAT)** to push to individual repositories. The default `GITHUB_TOKEN` only has permissions for the current repository.

## Solution: Create and Configure PAT

### Step 1: Create Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Configure the token:
   - **Name:** `ai_portfolio_v2_subtree_sync`
   - **Expiration:** 90 days (or custom)
   - **Scopes:** Check `repo` (Full control of private repositories)
4. Click **"Generate token"**
5. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Add Token as Repository Secret

1. Go to ai_portfolio_v2 repository settings:
   - https://github.com/vn6295337/ai_portfolio_v2/settings/secrets/actions
2. Click **"New repository secret"**
3. Configure:
   - **Name:** `PORTFOLIO_SYNC_TOKEN`
   - **Value:** Paste the token you copied
4. Click **"Add secret"**

### Step 3: Update Workflows (Already Done)

The workflows have been updated to use `PORTFOLIO_SYNC_TOKEN` instead of `GITHUB_TOKEN`:

```yaml
git remote add ai-land https://x-access-token:${{secrets.PORTFOLIO_SYNC_TOKEN}}@github.com/vn6295337/ai-land.git
```

### Step 4: Test the Workflow

After adding the secret:

1. Make a small change in ai-land:
   ```bash
   echo "test" >> ai-land/test.txt
   git add ai-land/test.txt
   git commit -m "Test workflow with PAT"
   git push origin main
   ```

2. Check workflow status:
   ```bash
   gh run list --repo vn6295337/ai_portfolio_v2 --limit 1
   ```

3. Verify file appears in https://github.com/vn6295337/ai-land

## Security Notes

- **Never commit the PAT** to the repository
- Store it only in GitHub Secrets
- Rotate the token every 90 days
- If compromised, revoke immediately at https://github.com/settings/tokens

## Troubleshooting

### Workflow still fails with 403 error
- Verify secret name is exactly `PORTFOLIO_SYNC_TOKEN`
- Check PAT has `repo` scope
- Ensure PAT hasn't expired

### Workflow doesn't run
- Check `.github/workflows/` files exist on GitHub
- Verify workflow is enabled in Actions tab
- Check trigger conditions match (push to `ai-land/**`)

## Token Expiration Handling

When token expires:
1. Generate new PAT (same steps above)
2. Update `PORTFOLIO_SYNC_TOKEN` secret with new value
3. No workflow changes needed

## Alternative: GitHub App (Advanced)

For production, consider using a GitHub App instead of PAT for better security and no expiration issues.
