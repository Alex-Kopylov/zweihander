# Content Matching Strategies

## Matching Criteria (Weighted)

### 1. Direct Match (40%)

Keywords overlap with JD/success profile, same domain/technology, same outcome type, same scale/complexity.

**Scoring:**
- 90-100%: Exact match (same skill, domain, context)
- 70-89%: Strong match (same skill, different domain)
- 50-69%: Good match (overlapping keywords, similar outcomes)
- <50%: Weak direct match

### 2. Transferable Skills (30%)

Same capability in different context, leadership in different domain, technical problem-solving in different stack, similar scale/complexity in different industry.

**Scoring:**
- 90-100%: Directly transferable (process, skill generic)
- 70-89%: Mostly transferable (some domain translation needed)
- 50-69%: Partially transferable (analogy required)
- <50%: Stretch to call transferable

### 3. Adjacent Experience (20%)

Touched on skill as secondary responsibility, used related tools/methodologies, worked in related problem space, supporting role in relevant area.

**Scoring:**
- 90-100%: Closely adjacent (just different framing)
- 70-89%: Clearly adjacent (related but distinct)
- 50-69%: Somewhat adjacent (requires explanation)
- <50%: Loosely adjacent

### 4. Impact Alignment (10%)

Achievement type matches role values: quantitative metrics (data-driven roles), team outcomes (collaboration roles), innovation (creative roles), scale (hyperscale roles).

**Scoring:**
- 90-100%: Perfect impact alignment
- 70-89%: Strong impact alignment
- 50-69%: Moderate impact alignment
- <50%: Weak impact alignment

## Overall Confidence Score

```
Overall = (Direct x 0.4) + (Transferable x 0.3) + (Adjacent x 0.2) + (Impact x 0.1)
```

**Confidence Bands:**
- 90-100%: DIRECT - Use with confidence
- 75-89%: TRANSFERABLE - Strong candidate
- 60-74%: ADJACENT - Acceptable with reframing
- 45-59%: WEAK - Consider only if no better option
- <45%: GAP - Flag as unaddressed requirement

## Content Reframing Strategies

Apply when match is >60% but language doesn't align with target terminology.

### Strategy 1: Keyword Alignment

Preserve meaning, adjust terminology.

```
Before: "Led experimental design and data analysis programs"
After:  "Led data science programs combining experimental design and statistical analysis"
Reason: Target role uses "data science" terminology
```

### Strategy 2: Emphasis Shift

Same facts, different focus.

```
Before: "Designed statistical experiments... saving millions in recall costs"
After:  "Prevented millions in potential recall costs through predictive risk detection using statistical modeling"
Reason: Target role values business outcomes over technical methods
```

### Strategy 3: Abstraction Level

Adjust technical specificity based on target role.

```
Before: "Built MATLAB-based automated system for evaluation"
After:  "Developed automated evaluation system"
Reason: Target role is language-agnostic, emphasize outcome

OR (if role values specificity):
After:  "Built automated evaluation system (MATLAB, Python integration)"
```

### Strategy 4: Scale Emphasis

Highlight relevant scale aspects.

```
Before: "Managed project with 3 stakeholders"
After:  "Led cross-functional initiative coordinating 3 organizational units"
Reason: Emphasize cross-org complexity over headcount
```

## Presentation Format

For each template slot, present top 3 matches:

```
TEMPLATE SLOT: {Role} - Bullet {N}
SEEKING: {Requirement description}

MATCHES:
[DIRECT - 95%] "{bullet_text}"
  Direct: {what matches directly}
  Transferable: {what transfers}
  Metrics: {quantified impact}
  Source: {resume_name}

[TRANSFERABLE - 78%] "{bullet_text}"
  Transferable: {what transfers}
  Adjacent: {what's adjacent}
  Gap: {what's missing}
  Source: {resume_name}

RECOMMENDATION: Use DIRECT match (95%)
```

## Gap Handling

When confidence < 60%:

**Option 1: Reframe Adjacent Experience**
Present reframing with before/after and truthfulness justification.

**Option 2: Flag for Cover Letter**
Acknowledge gap, emphasize learning ability in cover letter.

**Option 3: Omit Bullet Slot**
Reduce template allocation for that role.

**Option 4: Use Best Available with Disclosure**
Include best match with transparent confidence score.

**Option 5: Trigger Experience Discovery**
If not yet run, offer branching interview for the specific gap area.
