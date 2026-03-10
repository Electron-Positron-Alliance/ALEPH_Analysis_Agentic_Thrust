# Workflow Improvement Log

This file documents known gaps, inefficiencies, and suggested improvements to the agent-physicist collaboration workflow. It is updated at the end of sessions where a workflow problem is identified. Improvements are expected — this is not a solved problem.

Each entry: date, problem observed, suggested improvement, status.

---

## 2026-03-06 — Knowledge management across sessions and projects

### Problem 1: Skill files are static; discoveries are not automatically fed back

The skill files encode expert knowledge as of the time they were written. When the agent discovers something new during an analysis (e.g., a bug pattern, a new calibration number, a better workflow), it must manually update the skill files. There is no automated mechanism to propagate discoveries back. Over time, skill files can drift behind actual practice.

**Suggested improvement**: At the end of every session, the agent should explicitly check whether any finding in that session should update a skill file, and do so before closing. This should be a named step in the session close protocol. A future improvement would be a structured "skill file review" checkpoint at the end of major analysis milestones.

---

### Problem 2: Alliance synthesis lives in a per-repo file

`Plans/alliance_analysis_summaries.md` is inside `ALEPH_Agentic_Event_Shape_Analysis`. If a new analysis starts in a different repository, the agent would not automatically have access to this file without the physicist pointing to it explicitly.

**Suggested improvement**: The synthesis file (or a pointer to it) should live in the skills directory (`~/.claude/skills/aleph-ee-analysis/`) alongside the skill files, so it is always accessible regardless of which repo is active. Alternatively, the MEMORY.md file in the project memory directory could hold pointers to the synthesis. The current workaround is to ask the physicist to point to the file at session start.

**Current status**: File lives in `Plans/` inside the agentic repo. Agent must remember to check it.

---

### Problem 3: No mechanism to detect when a new alliance repo exists

The agent only learns about new repositories when the physicist mentions them. There is no way for the agent to discover that a new analysis has been started or published.

**Suggested improvement**: Maintain a canonical list of e+e- alliance repositories in a shared location (e.g., a GitHub organization README, or a text file on EOS). At session start, the agent could check this list against the Known Repositories registry and flag any new entries. This requires physicist agreement on a canonical location.

---

### Problem 4: Memory file has a 200-line context limit

The auto-memory `MEMORY.md` is truncated at 200 lines. Deep synthesis of multiple alliance analyses cannot fit there. The result is that inter-session knowledge relies on the physicist reminding the agent to read `Plans/alliance_analysis_summaries.md`.

**Suggested improvement**: Keep `MEMORY.md` as a pointer/index only (pointers to detailed synthesis files), with full content in named files. The session startup protocol already does this — MEMORY.md is kept brief, detail lives in Plans/. Ensure the startup protocol explicitly reads the Plans/ files, not just MEMORY.md.

---

### Problem 5: Knowledge transfer between projects is manual

When a new project starts (e.g., a C-parameter analysis in a new repo), the agent has no automatic way to bring along the alliance summaries, skill files, or workflow improvement log. The physicist must explicitly point the agent to these materials each time.

**Suggested improvement (longer term)**: Package the skill files + alliance summaries as a proper installable context that can be attached to any new project. In the short term: the physicist should include a "context bootstrap" step at the start of every new project — sharing the skill skill directory path and the alliance summaries file path explicitly.

---

*Add new entries at the end of any session where a workflow gap is observed.*
