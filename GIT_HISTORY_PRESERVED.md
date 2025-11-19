# Git History Preservation

This repository consolidates multiple sub-projects. Original git histories have been preserved as remote branches:

## Project History References

- **askme_v2**: `askme-repo/main` (66 commits)
- **ai-models-discoverer_v3**: `ai-models-repo/main`
- **ai-land-main**: `ai-land-repo/main`

To view the full history of any project:
```bash
git log askme-repo/main --oneline
git log ai-models-repo/main --oneline
git log ai-land-repo/main --oneline
```

To create a backup of original histories:
```bash
git show-ref
```

## Next Steps

1. The nested `.git` directories have been removed
2. All project files remain in their original directories
3. The root repository now tracks all projects as a single repo
4. Individual project histories are accessible via remote branches listed above
