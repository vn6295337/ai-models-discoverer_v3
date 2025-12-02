# ai_portfolio - GitHub Project Board Setup Instructions

**Date**: 2025-11-10
**Project**: ai_portfolio
**Purpose**: Track progress across all 85 checklist tasks

## Overview

GitHub Projects will be used to manage the portfolio transformation across 4 phases and 3 repositories.

## Setup Steps

### 1. Create Project Board (Manual Setup Required)

**GitHub CLI doesn't support project boards in this environment, so manual setup is required:**

1. Navigate to https://github.com/vn6295337
2. Click on "Projects" tab
3. Click "New project"
4. Choose "Table" template
5. Name: "ai_portfolio"
6. Description: "Track portfolio enhancement across askme, ai-models-discoverer_v3, and ai-land"

### 2. Configure Project Views

**Recommended Views:**

#### View 1: By Phase (Default)
- **Columns**: Status (Todo, In Progress, Done)
- **Grouping**: Phase (Phase 1, Phase 2, Phase 3, Phase 4)
- **Filter**: None
- **Sort**: Priority (High → Low), then Task Number

#### View 2: By Project
- **Columns**: Status
- **Grouping**: Repository (askme, discoverer, ai-land, portfolio)
- **Filter**: None
- **Sort**: Priority

#### View 3: High Priority Only
- **Columns**: Status
- **Grouping**: None
- **Filter**: Priority = High
- **Sort**: Due Date

### 3. Custom Fields to Add

1. **Phase** (Single select)
   - Phase 1: Foundation
   - Phase 2: Content & Polish
   - Phase 3: Portfolio Integration
   - Phase 4: Launch & Iteration

2. **Priority** (Single select)
   - High
   - Medium
   - Low

3. **Repository** (Single select)
   - askme
   - ai-models-discoverer_v3
   - ai-land
   - portfolio (landing page)
   - multiple (cross-cutting)

4. **Task Number** (Number)
   - Range: 1-85

5. **Effort (hours)** (Number)
   - Estimated hours for task

6. **Sub-phase** (Text)
   - E.g., "1A: Repository Audit", "2B: Visual Assets"

### 4. Link Existing Issues

**Link the 15 created issues to the project:**

**askme issues (#114-118):**
- #114: Add LICENSE file (Phase 1B, High)
- #115: Fix duplicate README content (Phase 1B, High)
- #116: Add visual assets (Phase 2B, Medium)
- #117: Enhance README (Phase 2A, Medium)
- #118: Add GitHub topics/badges (Phase 2C, Low)

**discoverer issues (#1-5):**
- #1: Add LICENSE file (Phase 1B, High)
- #2: Fix placeholder URL (Phase 1B, High)
- #3: Create visual assets (Phase 2B, Medium)
- #4: Enhance README (Phase 2A, Medium)
- #5: Add examples/metadata (Phase 2C, Low)

**ai-land issues (#4-8):**
- #4: Add LICENSE file (Phase 1B, High)
- #5: Major README expansion (Phase 2A, High)
- #6: Create screenshots/GIFs (Phase 2B, Medium)
- #7: Add examples/metadata (Phase 2C, Low)
- #8: [Optional] Modularization (Phase 2+, Optional)

### 5. Add Additional Cards for Non-Issue Tasks

**Create draft issues or cards for:**

**Phase 1A (Completed):**
- ✅ Task 1: Audit askme
- ✅ Task 2: Audit discoverer
- ✅ Task 3: Audit ai-land
- ✅ Task 4-6: Create GitHub Issues
- ✅ Task 7: Write portfolio goals
- ✅ Task 8: Create portfolio repo
- ✅ Task 9: Set up project boards

**Phase 1B (Remaining - Tasks 10-20):**
- Task 13-15: Review .gitignore files
- Task 16-18: Test builds on clean environment
- Task 19: Consolidate dependencies documentation
- Task 20: Standardize repository descriptions

**Phase 2A (Tasks 21-35):**
- Tasks for README overhaul (covered by issues #117, #4, #5)

**Phase 2B (Tasks 36-45):**
- Tasks for visual assets (covered by issues #116, #3, #6)
- Task 45: Create portfolio architecture diagram

**Phase 2C (Tasks 46-55):**
- Tasks for examples directories (covered by issues #118, #5, #7)
- Task 55: Set up GitHub Actions CI

**Phase 3A (Tasks 56-65):**
- Task 56: Write value proposition (partially done in portfolio README)
- Task 57-59: Create project summaries (done in portfolio README)
- Task 60: Write cohesive narrative (partially done)
- Task 61-63: Add personal branding
- Task 64-65: Design/deploy portfolio README

**Phase 3B (Tasks 66-75):**
- Task 66-68: Add "Other Projects" sections
- Task 69-71: Add portfolio links to READMEs
- Task 72-74: Add CTAs
- Task 75: Pin repos on profile

**Phase 4A (Tasks 76-80):**
- Task 76-79: Proofread all READMEs
- Task 80: Test installation on fresh environments

**Phase 4B (Tasks 81-85):**
- Task 81-83: Tag releases
- Task 84: Enable GitHub Pages
- Task 85: Update profile README

### 6. Set Up Automation (Optional)

**GitHub Projects supports automation rules:**

1. **Auto-move to In Progress**
   - When: Issue/PR is assigned
   - Then: Move to "In Progress"

2. **Auto-move to Done**
   - When: Issue is closed
   - Then: Move to "Done"

3. **Auto-add to project**
   - When: Issue is created in askme/discoverer/ai-land
   - Then: Add to "AI Portfolio Transformation" project

### 7. Milestones

**Create milestones in each repository:**

**askme:**
- Milestone: "Portfolio Enhancement"
- Due: 2 weeks
- Issues: #114, #115, #116, #117, #118

**discoverer:**
- Milestone: "Portfolio Enhancement"
- Due: 2 weeks
- Issues: #1, #2, #3, #4, #5

**ai-land:**
- Milestone: "Portfolio Enhancement"
- Due: 2 weeks
- Issues: #4, #5, #6, #7, (#8 optional)

## Project Board URL

Once created, the project board will be accessible at:
`https://github.com/users/vn6295337/projects/[PROJECT_NUMBER]`

**Repository**: https://github.com/vn6295337/ai_portfolio

## Progress Tracking

**Weekly updates:**
- Review completed tasks
- Update effort estimates
- Adjust priorities based on progress
- Document blockers

**Success Metrics:**
- Tasks completed per week: Target 10-12
- Issues closed per week: Target 2-3
- Phase completion rate: Track weekly

## Alternative: Local Tracking

If GitHub Projects setup is deferred, use the checklist file:
`/home/km_project/ai-portfolio-atomic-checklist.txt`

Update checkboxes and progress tracking section manually as tasks complete.

## Status

**Phase 1A: COMPLETED** ✅
- All 9 tasks completed
- 3 audits documented
- 15 GitHub issues created
- Portfolio goals written
- Landing page repository created

**Next**: Phase 1B (Infrastructure setup)
