---
expect:
  session_url: '/^https:..awen.press.review.[A-Za-z0-9_-]+$/'
  model: string
---

{"book_title": "The Salt Road", "section_count": 1, "rules": ["Read each section in order, as a first-time reader.", "Rate only what is on the page."], "guidance": "The author wants to know where attention drifts and whether the narrator earns the reader's trust.", "brief": "You are a beta-reader. Report your experience as a reader, not line edits.", "rubric": {"rating_overall": "1 = would stop reading, 5 = could not put it down", "r_clarity": "Could you follow what happened and why?", "r_pacing": "Did the section move at the right speed?", "r_voice": "Is the narrator's voice distinct and consistent?"}, "submission_schema": {"type": "object", "additionalProperties": false, "required": ["rating_overall", "would_keep_reading"], "properties": {"rating_overall": {"type": "integer", "minimum": 1, "maximum": 5}, "would_keep_reading": {"type": "boolean"}, "notes": {"type": "string"}, "r_clarity": {"type": "integer", "minimum": 1, "maximum": 5}, "r_pacing": {"type": "integer", "minimum": 1, "maximum": 5}, "r_voice": {"type": "integer", "minimum": 1, "maximum": 5}}}, "review": "rv_evalReviewValue0001", "next": "Call get_next_section with this review value."}
