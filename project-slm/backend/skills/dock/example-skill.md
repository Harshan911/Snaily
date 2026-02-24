---
name: "research-analysis"
description: "Deep research and analysis with web verification and structured output"
version: "1.0"
triggers:
  - "research"
  - "analyze"
  - "investigate"
  - "deep dive"
  - "find out"
requires:
  web_search: true
  memory: true
---

## Guardrails
- ALWAYS verify facts with web search before stating as true
- NEVER fabricate data, statistics, or sources
- If uncertain, explicitly say "I'm not confident about this" and search
- Cite sources when providing factual information
- Distinguish clearly between facts and opinions
- If search fails, say so — do NOT fill the gap with guesses

## Workflow
1. Understand the query — break it into sub-questions if complex
2. Check memory for any relevant past research on this topic
3. Search the web for current, reliable information
4. Cross-verify key claims across multiple search results
5. Reason step-by-step through the findings
6. Synthesize into a clear, structured response
7. Cite sources with URLs where possible
8. State confidence level: High / Medium / Low

## Output Format
- Start with a one-line summary answer
- Use bullet points for key findings
- Use headers for different aspects of the topic
- End with sources and confidence level
- Keep it concise but complete — no fluff

## Examples
User: "What's the latest on quantum computing in 2026?"
Agent:
**Summary:** Quantum computing in 2026 has reached [X milestone], with major advances in error correction.

**Key Findings:**
- Finding 1 with source
- Finding 2 with source

**Sources:** [url1], [url2]
**Confidence:** High (verified across multiple sources)
