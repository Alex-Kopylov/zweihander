---
name: spec-interview
argument-hint: [instructions]
description: Interview user in-depth to create a detailed spec
allowed-tools: AskUserQuestion, Write
---

Follow the user instructions and interview User in detail using the **AskUserQuestionTool** about technical implementation, API design, data models, prompt engineering pitfalls, LLM output quality concerns, and tradeoffs. Make sure the questions are not obvious - be very in-depth. Hunt and track any contradictions to resolve them. Continue interviewing User continually until it's complete. Then, write the spec to a file.

<instructions>$ARGUMENTS</instructions>
