# Claude skills for Corn & Culture Club

Built across Phases 1–4. Each is a properly formatted Claude skill (SKILL.md
with frontmatter) so a new edition is produced by conversation:

- ccc-research  (Phase 1, DONE) — coverage pipeline + editorial curation/discovery
                                    → data/editions/<date>/research.json
- ccc-writer    (Phase 2) — research.json → draft.md in house voice
- ccc-preview   (Phase 3) — draft.md → edition.html (email + web)
- ccc-publish   (Phase 4) — hand off to beehiiv (paste-ready HTML)

The editorial thesis (PLAN.md §2.5): calendars are the FLOOR. The value is
Discovery (non-obvious events) + Curation (POV, junk-cutting). Python does
coverage; the skills do the parts that need taste.
