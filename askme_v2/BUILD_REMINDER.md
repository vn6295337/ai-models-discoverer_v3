# APK Build Reminder - Dec 01, 2025

## Status
EAS Build quota resets on **December 01, 2025**.

## What to Do
When Dec 01 arrives, run the following command to build the APK with all critical fixes:

```bash
cd /home/km_project/askme_v2/askme-app
npx eas build --platform android --profile preview
```

## Critical Fixes Included
This build includes fixes for:
1. ✅ Blank screen after send (FlatList key stability)
2. ✅ Offline queueing not persisting (ID-based message updates)
3. ✅ Manual sync responses not appearing in chat (queue ID mapping)
4. ✅ Metadata not displaying (model/category/time)

## Details
- **Frontend commit:** 2a07a87
- **Backend commit:** 6f86555
- **Documentation:** See `askme-app/README.md` → "Recent Fixes (Nov 2025)" section
- **Last updated:** Nov 18, 2025

## After Build
1. Download APK from EAS Build dashboard
2. Install on Android device/emulator
3. Test all fixes:
   - Send queries and verify no blank screen
   - Offline mode: queue queries, verify they persist
   - Manual sync: verify responses appear in chat with metadata

---
**SET A REMINDER FOR DEC 01!**
