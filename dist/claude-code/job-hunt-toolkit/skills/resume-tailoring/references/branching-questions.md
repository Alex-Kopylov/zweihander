# Branching Experience Discovery Questions

## Overview

Use conversational discovery, not a static questionnaire; each answer informs the next question.

## Multi-Job Context

When running discovery for multiple jobs, provide context about which jobs the gap appears in:

**Template:**
```
"{SKILL} experience appears in {N} of your target jobs ({Company1}, {Company2}, ...).

This is a {HIGH/MEDIUM/LOW}-LEVERAGE gap - addressing it helps {N/some/one} application(s).

Current best match: {X}% confidence ('{best_match_text}')

{Standard branching question}"
```

**Leverage Classification:**
- HIGH-LEVERAGE: Appears in 3+ jobs (critical gaps)
- MEDIUM-LEVERAGE: Appears in 2 jobs (important gaps)
- LOW-LEVERAGE: Appears in 1 job (job-specific gaps)

## Technical Skill Gap Pattern

```
INITIAL PROBE:
"I noticed the job requires {SKILL}. Have you worked with {SKILL} or {RELATED_AREA}?"

BRANCH A - If YES (Direct Experience):
  -> "Tell me more - what did you use it for?"
  -> "What scale? {Relevant metric}?"
  -> "Was this production or development/testing?"
  -> "What specific challenges did you solve?"
  -> "Any metrics on {performance/reliability/cost}?"
  -> CAPTURE: Build detailed bullet

BRANCH B - If INDIRECT:
  -> "What was your role in relation to the {SKILL} work?"
  -> "Did you {action1}, {action2}, or {action3}?"
  -> "What did you learn about {SKILL}?"
  -> ASSESS: Transferable experience?
  -> CAPTURE: Frame as support/enabling role if substantial

BRANCH C - If ADJACENT:
  -> "Tell me about your {ADJACENT_TECH} experience"
  -> "Did you do {relevant_activity}?"
  -> ASSESS: Close enough to mention?
  -> CAPTURE: Frame as related expertise

BRANCH D - If PERSONAL/LEARNING:
  -> "Any personal projects, courses, or self-learning?"
  -> "What did you build or deploy?"
  -> "How recent was this?"
  -> ASSESS: Strong enough if recent and substantive
  -> CAPTURE: Consider if gap critical

BRANCH E - If COMPLETE NO:
  -> "Any other {broader_category} work?"
  -> If yes: Explore that
  -> If no: Move to next gap
```

## Soft Skill / Experience Gap Pattern

```
INITIAL PROBE:
"The role emphasizes {SOFT_SKILL}. Tell me about times you've {demonstrated_that_skill}."

BRANCH A - If STRONG EXAMPLE:
  -> "What {entities} were involved?"
  -> "What was the challenge?"
  -> "How did you {drive_outcome}?"
  -> "What was the result? Metrics?"
  -> "Any {obstacle} you had to navigate?"
  -> CAPTURE: Detailed bullet with impact

BRANCH B - If VAGUE/UNCERTAIN:
  -> "Let me ask differently - have you ever {reframed_question}?"
  -> "What was that situation?"
  -> "How many {stakeholders}?"
  -> "What made it challenging?"
  -> CAPTURE: Help articulate clearly

BRANCH C - If PROJECT-SPECIFIC:
  -> "Tell me more about that project"
  -> "What was your role vs. others?"
  -> "Who did you coordinate with?"
  -> "How did you ensure alignment?"
  -> ASSESS: Enough depth?
  -> CAPTURE: Frame as leadership if substantial

BRANCH D - If VOLUNTEER/SIDE WORK:
  -> "Interesting - tell me more"
  -> "What was scope and timeline?"
  -> "What skills relate to this job?"
  -> "Measurable outcomes?"
  -> ASSESS: Relevant enough?
  -> CAPTURE: Include if demonstrates capability
```

## Recent Work Probe Pattern

```
INITIAL PROBE:
"What have you been working on in the last 6 months that isn't in your resumes yet?"

BRANCH A - If DESCRIBES PROJECT:
  -> "Tell me more - what was your role?"
  -> "What technologies/methods?"
  -> "What problem were you solving?"
  -> "What was the impact?"
  -> CHECK: "Does this address {gap_area}?"
  -> CAPTURE: Create bullet if substantive

BRANCH B - If MENTIONS MULTIPLE:
  -> "Let's explore each. Starting with {first}..."
  -> Go through systematically
  -> Prioritize by gap relevance
  -> CAPTURE: Multiple bullets if relevant

BRANCH C - If "NOTHING NEW":
  -> "What about small improvements, process changes, learning?"
  -> "New tools or technologies?"
  -> "Mentoring, teaching, knowledge sharing?"
  -> "Anything that might seem too small?"
  -> CAPTURE: Even small items can fill gaps
```

## Key Principles

1. **Start Broad, Go Narrow** - initial question is open-ended; follow-ups drill into specifics based on what they share
2. **Listen and Branch Dynamically** - promising answer: explore deeper; "no" answer: try adjacent or move on; unclear: rephrase
3. **Adapt to Communication Style** - verbose users: ask for key takeaway; terse users: provide examples; uncertain users: validate and offer prompts
4. **Recognize When to Move On** - after 2-3 attempts with nothing, gracefully move on; some gaps are acceptable
5. **Cross-Reference During Discovery** - connect experiences across gaps ("Earlier you mentioned X, does that relate here?")

## Capture Structure

For each discovered experience:

```markdown
### Experience: {Brief description}
- **Context:** {Where/when}
- **Scope:** {Scale, duration, impact}
- **Metrics:** {Quantified results}
- **Addresses:** {Which gaps / which jobs}
- **Confidence Improvement:** {Before% -> After%}
- **Bullet Draft:** "{Achievement-focused bullet}"
- **Integration Decision:** [Pending user approval]
```

## Example Complete Flow

```
SKILL: "I see the job requires CI/CD experience. Have you worked with CI/CD pipelines?"

USER: "Yes, I set up GitHub Actions for my side project."

SKILL: "Tell me more about that - what does the pipeline do?"

USER: "It runs tests and deploys to cloud when I push code."

SKILL: "What testing framework do you use?"

USER: "pytest for my Python code."

SKILL: "What's deployed - is this a production app?"

USER: "Yeah, it's a tool used by 3 nonprofits right now."

SKILL: "That's substantial! Have you dealt with any flaky tests or reliability issues?"

USER: "Actually yes, I had to add retries for some API-dependent tests."

SKILL: "Any metrics on build time or deployment frequency?"

USER: "Deploys take about 3 minutes, and I deploy several times a week."

[CAPTURED: Hands-on CI/CD, pytest, flaky test handling, production deployment.
 Directly fills gap with concrete details.]
```
