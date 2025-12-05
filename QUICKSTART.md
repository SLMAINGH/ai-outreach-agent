# 🚀 Quick Start Guide

## What You Got

**Production-ready LinkedIn outreach agent with:**
1. ✅ **Verbalized Sampling** - Generates 5 diverse message variants, picks best
2. ✅ **YAML configs** - Non-devs can change prompts, tone, models
3. ✅ **Batch processing** - Handle 100s of profiles with one command
4. ✅ **Simple code** - 340 lines, easy to modify

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."

# Or use .env file
echo "OPENAI_API_KEY=sk-..." > .env
echo "PERPLEXITY_API_KEY=pplx-..." >> .env
```

---

## Usage

### Single Profile
```bash
python production_simple.py
```

Output:
```
🎯 LinkedIn Outreach Agent (with Verbalized Sampling)
============================================================
Model: gpt-4o
Tone: genuine and conversational
CTA Style: casual coffee chat
Generating 5 variants per profile, selecting best

============================================================
🔍 Processing https://linkedin.com/in/sarah-chen...
✓ Success

============================================================
🎯 FINAL RESULT:
============================================================
SELECTED MESSAGE:
Hey Sarah! Saw your AI Infrastructure Summit talk on scaling vector
DBs—the query optimization for 1B+ QPS was mind-blowing. DataScale's
$50M Series B seems perfectly timed for your hiring push. Coffee in
SF to chat about productionizing LLM infrastructure?

WHY THIS ONE (Score: 9/10):
Most specific references (named conference, cited metric, included
funding amount). Natural peer-to-peer tone. Strong hook. Clear CTA.

WHY NOT OTHERS:
Variant 1 too generic, Variant 2 weak CTA, Variant 3 too formal...

✅ Done!
```

### Batch Mode
```python
# Edit production_simple.py, uncomment at bottom:

urls = [
    "https://linkedin.com/in/person1",
    "https://linkedin.com/in/person2",
    "https://linkedin.com/in/person3"
]
batch_outreach(urls, output_file="results.csv")
```

```bash
python production_simple.py
```

Output CSV:
```csv
url,success,message,error
https://linkedin.com/in/person1,True,"Hey John! Saw your post about...",
https://linkedin.com/in/person2,True,"Sarah - your AI Summit talk...",
https://linkedin.com/in/person3,False,,API rate limit exceeded
```

---

## Debug Options

**See what's happening under the hood!** All controlled via `config.yaml`:

```yaml
output:
  verbose: true              # Progress messages (always on)
  debug_mode: false          # 🔥 See EVERYTHING (all LLM calls)
  show_all_variants: false   # See all 5 message variants
  show_prompts: false        # See prompts sent to LLMs
  show_tool_calls: false     # See tool execution flow
```

**Quick examples:**

**See all 5 variants before supervisor picks:**
```yaml
output:
  show_all_variants: true
```

**Full debug mode (troubleshooting):**
```yaml
output:
  debug_mode: true
  show_tool_calls: true
```

For detailed guide: **See `DEBUG_OPTIONS.md`**

---

## Configuration (config.yaml)

### Change Models
```yaml
models:
  generator:
    model: "gpt-4o-mini"  # 10x cheaper than gpt-4o
    temperature: 0.8      # Higher = more creative
```

### Change Tone
```yaml
message_rules:
  tone: "casual and friendly"  # or "professional but approachable"
  cta_style: "15-min quick call"  # or "casual coffee chat"
```

### Batch Settings
```yaml
batch:
  delay_seconds: 3  # Wait 3s between profiles (avoid rate limits)
  stop_on_error: false  # Continue even if one fails
```

---

## Prompts (prompts.yaml)

### Change Message Generation
```yaml
tools:
  generate_message_variants: |
    Generate 5 diverse messages...

    RULES:
    1. Reference 2+ profile details  # Change to 3+ for more specificity
    2. Reference 1+ research insight
    3. Under 100 words  # Change to 75 for shorter messages
```

### Change Selection Criteria
```yaml
tools:
  select_best_message: |
    CRITERIA:
    1. Specificity
    2. Relevance
    3. Natural tone  # Add: 4. Humor (if that's your style)
```

### Add Examples
```yaml
good_examples:
  - message: "Your example here..."
    why_good: "Because..."

# Show these to your team to calibrate quality
```

---

## Common Changes for Agencies

### Client A: Tech Startups (Casual)
```yaml
# config.yaml
message_rules:
  tone: "casual and friendly - like reaching out to a peer"
  cta_style: "casual coffee chat"
  max_words: 80  # Shorter, punchier
```

### Client B: Finance/Enterprise (Professional)
```yaml
# config.yaml
message_rules:
  tone: "professional but approachable - respectful of seniority"
  cta_style: "15-min scheduled call"
  max_words: 100  # Slightly longer, more context
```

### Client C: Cost-Conscious
```yaml
# config.yaml
models:
  generator:
    model: "gpt-4o-mini"  # 10x cheaper
  agent:
    model: "gpt-4o-mini"  # Use mini for everything

# Or in prompts.yaml - generate 3 variants instead of 5
generate_message_variants: |
  Generate 3 different messages...  # Was 5
```

---

## File Structure

```
project/
├── production_simple.py      # Main code (340 lines)
├── config.yaml              # Models, tone, batch settings
├── prompts.yaml             # All prompts (easy to edit)
├── requirements.txt         # Dependencies
├── VERBALIZED_SAMPLING.md   # Deep dive on the technique
├── QUICKSTART.md           # This file
└── results.csv             # Output from batch mode
```

**Who edits what:**
- **Developers:** `production_simple.py`, `requirements.txt`
- **Account managers:** `config.yaml` (tone, CTA style)
- **Copywriters:** `prompts.yaml` (message rules, examples)
- **Everyone:** Uses `results.csv` for reporting

---

## Advanced Usage

### Load Different Configs
```python
# For different clients
CONFIG = load_config("config_client_techcorp.yaml")
PROMPTS = load_prompts("prompts_casual_tone.yaml")
```

### Show All Variants (Manual Pick)
```python
# Modify production_simple.py:
variants = generate_message_variants(profile, research)

# Parse and show all 5
print("VARIANT 1:", variant1)
print("VARIANT 2:", variant2)
...

choice = input("Pick 1-5: ")
# Use chosen variant
```

### Add Custom Fields
```python
# In mock_linkedin_scraper() or your real API:
return {
    "name": "John Doe",
    ...
    "custom_field": "Your agency-specific data"
}

# Then use in prompts.yaml:
generate_message_variants: |
  Custom context: {custom_field}
```

---

## Troubleshooting

### "FileNotFoundError: config.yaml"
```bash
# Make sure you're running from the right directory
cd /path/to/ai_agent_smart_af
python production_simple.py
```

### "⚠️ OPENAI_API_KEY not set!"
```bash
# Set environment variables
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."

# Or create .env file (needs python-dotenv)
echo "OPENAI_API_KEY=sk-..." > .env
```

### "Rate limit exceeded"
```yaml
# In config.yaml, increase delay:
batch:
  delay_seconds: 5  # Wait longer between profiles
```

### "Messages are too generic"
```yaml
# In prompts.yaml, make rules stricter:
generate_message_variants: |
  RULES:
  1. Reference 3+ SPECIFIC profile details (was 2+)
  2. Reference 2+ SPECIFIC research insights (was 1+)
  3. Must include at least one number/date
```

---

## Monitoring Quality

### Check Selector Scores
```python
# The selector returns a score 1-10
# Track average score over batches

scores = []
for result in results:
    # Parse score from result["message"]
    score = extract_score(result["message"])
    scores.append(score)

avg_score = sum(scores) / len(scores)
print(f"Average quality: {avg_score}/10")

# If avg < 7, tweak prompts or use better model
```

### A/B Test Configs
```bash
# Generate 50 with casual tone
python production_simple.py --config casual.yaml --output casual.csv

# Generate 50 with professional tone
python production_simple.py --config professional.yaml --output prof.csv

# Send both, track response rates
# Winner = your new default!
```

---

## Cost Estimates

### Per Message (with Verbalized Sampling):
- **GPT-4o:** ~$0.025 per profile (5 variants + selection)
- **GPT-4o-mini:** ~$0.0025 per profile (10x cheaper)

### For 100 Profiles:
- **GPT-4o:** ~$2.50
- **GPT-4o-mini:** ~$0.25

### Plus Perplexity (research):
- **Sonar Large:** ~$0.01 per profile
- **Total (100 profiles):** $2.50-3.50 with GPT-4o, $0.35 with mini

---

## Next Steps

### Week 1: Test with 10 Profiles
```bash
# Use real LinkedIn URLs from your CRM
urls = [
    "https://linkedin.com/in/prospect1",
    "https://linkedin.com/in/prospect2",
    ...
]

batch_outreach(urls, "test_batch.csv")

# Manually review all 10 messages
# Adjust prompts based on what you see
```

### Week 2: Tune for Your Style
```yaml
# Adjust tone, CTA, rules in config.yaml and prompts.yaml
# Re-run test batch
# Compare to Week 1 results
```

### Week 3: Scale to 100+
```bash
# Once quality is good, batch process your full list
# Track response rates
# Iterate on prompts based on what gets replies
```

### Week 4: Client-Specific Configs
```bash
# Create client1.yaml, client2.yaml, etc.
# Each client gets custom tone/style
# Non-devs can manage these configs
```

---

## Support

**Questions?** Check these docs:
- `VERBALIZED_SAMPLING.md` - How the sampling works
- `prompts.yaml` - See examples of good/bad messages
- Original code in repo for comparison

**Need help?** Ask your dev team to:
- Add more tools (email scraper, CRM integration)
- Create web UI for non-devs
- Set up automated scheduling
- Add analytics dashboard

---

## TL;DR for Non-Devs

### To change tone/style:
1. Open `config.yaml`
2. Change `tone:` and `cta_style:`
3. Save and re-run

### To change what makes a "good" message:
1. Open `prompts.yaml`
2. Edit the `RULES:` section
3. Add `good_examples:` and `bad_examples:`
4. Save and re-run

### To process your list:
1. Open `production_simple.py`
2. Find the `# Or batch mode` section at bottom
3. Uncomment it and paste your URLs
4. Run: `python production_simple.py`
5. Get results in CSV

**No coding required!** ✅
