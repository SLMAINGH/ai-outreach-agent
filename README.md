# AI Outreach Agent

Multi-agent system for LinkedIn outreach with Verbalized Sampling and quality feedback loops.

---

## Architecture

### Agent System

**Supervisor Pattern:** Central agent coordinates specialized sub-agents, evaluates outputs, and can retry with feedback.

**Sub-Agents:**
1. **Scraper Agent** - Extracts LinkedIn profile data
2. **Research Agent** - Company research via Perplexity (real-time web search)
3. **Generator Agent** - Produces 5 message variants using Verbalized Sampling
4. **Selector Agent** - Evaluates variants and picks best

**Feedback Loop:** Supervisor can reject outputs, provide specific feedback, and re-invoke sub-agents with improved prompts.

### Verbalized Sampling

Addresses LLM "mode collapse" (tendency to generate generic responses):
- Generate 5 variants with explicit probability distributions
- Sample from distribution tails (p < 0.10) for creative outputs
- Supervisor evaluates all variants against quality criteria
- Results in 1.6-2.1x more creative outputs ([research](https://www.verbalized-sampling.com))

### Quality Gates

Each step can be rejected and retried:
```
scrape_profile() → review() → [PASS: continue | REJECT: retry with feedback]
research_company() → review() → [PASS: continue | REJECT: retry with enhanced query]
generate_variants() → review() → [PASS: continue | REJECT: retry with stricter criteria]
```

Supervisor tracks attempts and can:
- Modify prompts based on failure analysis
- Adjust parameters (temperature, sampling strategy)
- Provide explicit examples of desired output
- Escalate to human review after N attempts

---

## Quick Start

### Standalone Mode

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."
python main.py
```

### API Mode (Clay Integration)

```bash
# Deploy to Railway
git push

# API receives employee lists, scores them, generates messages
# Returns results via webhooks
```

See [API.md](API.md) for Clay integration details.

---

## Configuration

All settings in `config.yaml` and `prompts.yaml`:

**Models:**
```yaml
models:
  agent: {model: "gpt-4o", temperature: 0}
  generator: {model: "gpt-4o", temperature: 0.7}
  research: {model: "sonar-pro"}
```

**Message Rules:**
```yaml
message_rules:
  max_words: 100
  required_profile_references: 2
  required_research_references: 1
  tone: "genuine and conversational"
```

**API Settings:**
```yaml
api:
  max_targets_per_company: 3
  min_score_threshold: 70
  delay_between_companies: 5
```

**Debug Options:**
```yaml
output:
  debug_mode: false           # Full LangChain debug output
  show_all_variants: false    # Display all 5 variants before selection
  show_prompts: false         # Display prompts sent to LLMs
  show_tool_calls: false      # Display tool execution details
```

---

## Agent Workflow

### 1. Profile Extraction
```python
profile = scrape_linkedin_profile(url)
# Returns: name, title, company, experience, recent activity
```

### 2. Company Research
```python
research = research_company(company, context=profile_insights)
# Perplexity searches: funding, hiring, challenges, tech initiatives
```

### 3. Message Generation (Verbalized Sampling)
```python
variants = generate_message_variants(profile, research)
# Generates 5 diverse variants:
# - Different hooks (question/observation/compliment)
# - Different profile details emphasized
# - Different research insights
# - Different formality levels
# - Different CTA styles
```

**Example Variants:**
```
Variant 1 (p=0.08): "Saw your AI Summit talk on vector DBs..."
Variant 2 (p=0.06): "Your post about RAG scaling hit home..."
Variant 3 (p=0.09): "That 1B+ QPS optimization stat was wild..."
Variant 4 (p=0.05): "DataScale's $50M Series B timing seems perfect..."
Variant 5 (p=0.07): "Your Meta experience with rec systems at scale..."
```

### 4. Supervisor Selection
```python
selected = select_best_message(variants, profile, research)
# Evaluates against:
# - Specificity (concrete details, not generic)
# - Relevance (timely, contextual)
# - Natural tone (human, not templated)
# - Strong hook (compelling opening)
# - Clear CTA (obvious next step)
```

**Output:**
```
SELECTED MESSAGE:
Saw your AI Summit talk on vector DBs—the 1B+ QPS optimization was impressive.
DataScale's $50M Series B seems timed for your hiring push. Coffee in SF?

SCORE: 9/10

REASONING:
- Most specific references (conference, metric, funding with date)
- Natural peer-to-peer tone
- Strong technical hook
- Clear, casual CTA

REJECTED:
Variant 2: Generic opening
Variant 3: Weak CTA
Variant 4: Too formal
Variant 5: Sales-y language
```

---

## Feedback Loops

### Retry with Enhanced Prompts

If supervisor rejects output, it can:

**1. Provide specific feedback:**
```python
if review.rejected:
    feedback = "Too generic. Must reference specific recent activity with dates."
    # Retry with feedback injected into prompt
    variants = generate_message_variants(
        profile,
        research,
        previous_feedback=feedback
    )
```

**2. Adjust parameters:**
```python
if variants_too_similar:
    temperature = 0.9  # Increase creativity
    num_variants = 7   # Generate more options
```

**3. Add examples:**
```python
if quality_low:
    prompt += """
GOOD EXAMPLE:
"Saw your talk at AI Summit on vector DB optimization. That 1B+ QPS stat was wild."

BAD EXAMPLE:
"I noticed you work in AI. Would love to connect."
"""
```

### Multi-Level Retry Strategy

```python
# Attempt 1: Standard generation
variants = generate_variants(profile, research)

# Review fails
if score < 7:
    # Attempt 2: Add specificity requirement
    variants = generate_variants(
        profile,
        research,
        rules="Must include 2 specific dates/numbers"
    )

# Still fails
if score < 7:
    # Attempt 3: Provide failed example + correction
    variants = generate_variants(
        profile,
        research,
        failed_example=previous_output,
        correction="This was too generic. Be more specific about..."
    )

# Max retries
if attempts >= 3:
    escalate_to_human_review()
```

---

## Clay Integration

Flask API with queue system for processing employee lists from Clay.

**Flow:**
1. Clay sends list of employees (same company)
2. API queues request (prevents rate limits)
3. Research company once (shared across all employees)
4. Score each employee (0-100) based on:
   - Seniority/decision-making power (30%)
   - Role relevance (25%)
   - Profile completeness (20%)
   - Response likelihood (25%)
5. Select top N (default: 3 with score >= 70)
6. Generate personalized messages for selected
7. Send results to webhook (one POST per employee)

**Scoring Example:**
```
Mark Otieno (CTO): 95/100 → SELECTED
  Reasoning: C-level with strong technical background, active on LinkedIn,
  relevant experience in digital transformation

Robin Hoffmann (CTO): 90/100 → SELECTED
  Reasoning: C-level role, focuses on tech innovation, profile indicates
  decision-making authority

Karen Scholl (VP Digital): 75/100 → SELECTED
  Reasoning: Senior role with digital focus, complete profile, relevant
  experience but slightly lower response likelihood

Eddie Wright (Director): 68/100 → NOT SELECTED
  Reasoning: Director-level but incomplete profile, below threshold

Diane Jones (Director): 65/100 → NOT SELECTED
  Reasoning: Generic title, limited profile information

Kenneth Mitchell (CMO): 60/100 → NOT SELECTED
  Reasoning: CMO role less relevant to technical offering
```

**Webhook Response:**
```json
{
  "vmid": "...",
  "fullName": "Mark Otieno",
  "title": "Chief Technology Officer",
  "selected": true,
  "selection_reasoning": "Score: 95/100. CTO with strong digital transformation background...",
  "message": "Saw your AI Summit talk on vector DBs...",
  "message_score": 9,
  "error": ""
}
```

See [API.md](API.md) for detailed API documentation.

---

## Cost Analysis

**Per Profile (Verbalized Sampling):**
- Research (Perplexity Sonar): $0.01
- Generation (GPT-4o, 5 variants): $0.025
- Selection (GPT-4o): $0.005
- **Total: $0.04 per profile**

**Using GPT-4o-mini:**
- Generation: $0.0025
- Selection: $0.0005
- **Total: $0.005 per profile** (8x cheaper)

**Batch Processing (100 profiles):**
- GPT-4o: $4.00
- GPT-4o-mini: $0.50

**Clay API Mode (per company, 6 employees, 3 selected):**
- Company research: $0.01 (once)
- Employee scoring: $0.005
- Message generation: $0.075 (3 × $0.025)
- **Total: $0.09 per company**

---

## Technical Details

**Stack:**
- LangChain v1 with `create_agent`
- OpenAI GPT-4o (generation, selection)
- Perplexity Sonar (research)
- Pydantic (structured outputs, validation)
- Flask (API mode)
- YAML (configuration)

**Structured Outputs:**
All LLM calls return Pydantic models:
```python
class OutreachMessage(BaseModel):
    message: str
    profile_references: list[str]
    research_references: list[str]
    quality_score: int

class SelectedMessage(BaseModel):
    message: str
    reason: str
    rejected_reasons: str
    score: int
```

**State Management:**
- Standalone: In-memory (no persistence)
- API: Queue-based with background worker thread
- Optional: Add checkpointing for long-running workflows

---

## Project Structure

```
├── main.py                   # Standalone CLI agent
├── api.py                    # Flask API for Clay integration
├── config.yaml              # All configuration
├── prompts.yaml             # All prompts and examples
├── requirements.txt         # Dependencies
├── Procfile                 # Railway deployment config
├── README.md               # This file
├── API.md                  # API documentation
├── QUICKSTART.md           # Usage guide
├── DEBUG_OPTIONS.md        # Debug configuration
└── VERBALIZED_SAMPLING.md  # Technical deep dive
```

---

## Customization

### Add New Sub-Agent

```python
@tool
def analyze_sentiment(message: str) -> str:
    """Analyze message tone."""
    llm = ChatOpenAI(model="gpt-4o")
    result = llm.invoke([HumanMessage(content=f"Analyze tone: {message}")])
    return result.content

# Add to agent tools
agent = create_agent(
    model=llm,
    tools=[scrape, research, generate, select, analyze_sentiment]
)
```

### Modify Supervisor Logic

```python
# In prompts.yaml
supervisor:
  system: |
    You coordinate sub-agents.

    WORKFLOW:
    1. scrape_profile(url)
    2. research_company(company)
    3. generate_variants(profile, research)
    4. analyze_sentiment(variants)  # NEW STEP
    5. select_best_message(variants, sentiment_analysis)

    QUALITY GATES:
    - Reject if sentiment score < 0.7
    - Reject if variants have < 3 diversity score
    - Max 2 retries per step
```

### Custom Feedback Loop

```python
def generate_with_retry(profile, research, max_attempts=3):
    for attempt in range(max_attempts):
        variants = generate_variants(profile, research)
        review = review_quality(variants)

        if review.approved:
            return variants

        # Inject feedback into next attempt
        research += f"\nPREVIOUS FEEDBACK: {review.feedback}"

    return None  # Failed after max attempts
```

---

## Debug Options

Control verbosity via `config.yaml`:

```yaml
output:
  verbose: true              # Progress messages
  debug_mode: false          # Full LangChain trace
  show_all_variants: false   # Display all 5 options
  show_prompts: false        # Display prompts
  show_tool_calls: false     # Display tool execution
```

**Example with `show_all_variants: true`:**
```
ALL 5 VARIANTS GENERATED:
============================================================
<response>
  <message>Saw your AI Summit talk...</message>
  <probability>0.08</probability>
  <hook_type>observation</hook_type>
</response>
<response>
  <message>Your post about RAG...</message>
  <probability>0.06</probability>
  <hook_type>question</hook_type>
</response>
... (3 more)
============================================================

SUPERVISOR'S SELECTION:
Variant 1
Score: 9/10
Reasoning: Most specific references, natural tone, strong hook
```

See [DEBUG_OPTIONS.md](DEBUG_OPTIONS.md) for complete guide.

---

## Deployment

### Railway

```bash
# Procfile automatically runs:
gunicorn api:app --bind 0.0.0.0:$PORT --timeout 600 --workers 2

# Set environment variables:
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...
```

### Local

```bash
# Standalone
python main.py

# API mode
python api.py
```

---

## References

- [Verbalized Sampling Paper](https://www.verbalized-sampling.com)
- [LangChain Documentation](https://python.langchain.com)
- [Supervisor Pattern](https://python.langchain.com/docs/tutorials/agents/)

---

## License

MIT
