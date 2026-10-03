# 20 — G10 in-engine verification: glass and zone reflections, BEFORE vs AFTER

Status: IN PROGRESS (2026-10-03). Harness written; first run pending.

Plan:
- Harness: `<clone>/Assets/Editor/Audit/FrontRoomsGlassG10Capture.cs` (private clone `proj_glass` only), built from
  the audit harness (`interaction_audit/harness/FrontRoomsInteractionAudit.cs.txt`): same scene, seed 4242, title
  handoff, target search and game camera (1920x1080, 4x MSAA, full post).
- Per view, one frozen moment (Time.timeScale 0), three states: A BEFORE (shipped), B AFTER-glass (Glass_Window +
  zone cube, scene ambient), C AFTER (B + `FrontRoomsLook.ApplyAmbient()`), plus a no-pane reference for window views.
- Views: audit frames 01, 04, 23, 34, 35, 37 (dark) + a dead-lamp cell; windows in Level 0 and Office at 1.5 m
  head-on, ~50°, steep, 0.7 m; glass props.
