# 🐛 Debug Options Guide

All debug options are controlled via `config.yaml` - no code changes needed!

---

## Quick Reference

```yaml
# config.yaml
output:
  verbose: true              # Progress messages (on by default)
  debug_mode: false          # 🔥 FULL DEBUG - all LLM calls
  show_all_variants: false   # See all 5 message variants
  show_prompts: false        # See prompts sent to LLMs
  show_tool_calls: false     # See tool execution details
```

---

## Options Explained

### 1. `verbose: true` (Default)

**What it shows:**
```
🔍 Processing https://linkedin.com/in/sarah-chen...
✓ Success

[1/3] https://linkedin.com/in/person1
✓ Success
```

**When to use:** Always on for normal operation

---

### 2. `debug_mode: true` (Most Powerful)

**What it shows:** EVERYTHING - every LLM call, prompt, response, tool execution

**Example output:**
```
🐛 Debug mode enabled - showing all LLM calls

[chain/start] [1:chain:AgentExecutor] Entering Chain run with input:
{
  "messages": [
    {
      "role": "user",
      "content": "https://linkedin.com/in/sarah-chen"
    }
  ]
}
[llm/start] [1:chain:AgentExecutor > 2:llm:ChatOpenAI] Entering LLM run with input:
{
  "messages": [
    [
      {
        "role": "system",
        "content": "You generate personalized LinkedIn outreach..."
      }
    ]
  ]
}
[llm/end] [1:chain:AgentExecutor > 2:llm:ChatOpenAI] Output:
{
  "generations": [[{"text": "..."}]]
}
[tool/start] [1:chain:AgentExecutor > 3:tool:scrape_linkedin_profile] Entering Tool run
[tool/end] [1:chain:AgentExecutor > 3:tool:scrape_linkedin_profile] Output: "NAME: Sarah Chen..."
...
```

**When to use:**
- Debugging why agent isn't working
- Understanding full execution flow
- Seeing exact prompts/responses

**Warning:** VERY verbose output (100s of lines)

---

### 3. `show_all_variants: true`

**What it shows:** All 5 message variants before supervisor picks

**Example output:**
```
============================================================
📝 ALL 5 VARIANTS GENERATED:
============================================================
<response>
  <message>Hey Sarah! Saw your AI Infrastructure Summit talk on scaling
  vector DBs—the query optimization for 1B+ QPS was mind-blowing...</message>
  <probability>0.08</probability>
  <profile_details_used>AI Infrastructure Summit talk, vector databases, 1B+ QPS</profile_details_used>
  <research_insights_used>$50M Series B, hiring push</research_insights_used>
  <hook_type>observation</hook_type>
</response>

<response>
  <message>Sarah - your post about RAG scaling challenges hit home.
  We're wrestling with the same vector DB bottlenecks...</message>
  <probability>0.06</probability>
  <profile_details_used>RAG post, vector DB expertise</profile_details_used>
  <research_insights_used>scaling challenges</research_insights_used>
  <hook_type>question</hook_type>
</response>

... [3 more variants] ...
============================================================

SELECTED MESSAGE:
Hey Sarah! Saw your AI Infrastructure Summit talk...

WHY THIS ONE (Score: 9/10):
Most specific references...
```

**When to use:**
- Testing if variants are diverse enough
- Seeing what the supervisor is choosing from
- Quality checking message generation
- A/B testing different variants

**Pro tip:** Copy all 5 variants, manually send different ones to different prospects, track which gets best response

---

### 4. `show_prompts: true`

**What it shows:** Every prompt sent to LLMs and their responses

**Example output:**
```
🤔 Calling ChatOpenAI...
────────────────────────────────────────────────────────────
PROMPT:
<instructions>
Generate 5 different personalized LinkedIn outreach messages,
each within a separate <response> tag. Each <response> must
include a <message> and a numeric <probability>. Please sample
at random from the tails of the distribution...
</instructions>

PROFILE DATA:
NAME: Sarah Chen
TITLE: VP Engineering
...
────────────────────────────────────────────────────────────

✓ Response received (2847 chars)
OUTPUT: <response><message>Hey Sarah!...</message>...
```

**When to use:**
- Debugging prompt quality
- Checking if context is being passed correctly
- Understanding why output is wrong
- Tweaking prompts in `prompts.yaml`

---

### 5. `show_tool_calls: true`

**What it shows:** When tools are called and their inputs/outputs

**Example output:**
```
🔧 Using tool: scrape_linkedin_profile
   Input: {'linkedin_url': 'https://linkedin.com/in/sarah-chen'}
✓ Tool complete
   Output: NAME: Sarah Chen
TITLE: VP Engineering
COMPANY: DataScale AI...

🔧 Using tool: research_company
   Input: {'company': 'DataScale AI', 'title': 'VP Engineering', 'context': '15+ years ML infrastructure'}
✓ Tool complete
   Output: DataScale AI raised $50M Series B in November 2024...

🔧 Using tool: generate_message_variants
   Input: {'profile_data': 'NAME: Sarah Chen...', 'research_data': 'DataScale AI raised...'}
✓ Tool complete

🔧 Using tool: select_best_message
   Input: {'variants': '<response>...', 'profile_data': '...', 'research_data': '...'}
✓ Tool complete
   Output: SELECTED MESSAGE: Hey Sarah! Saw your AI...
```

**When to use:**
- Understanding execution flow
- Seeing what data is passed between tools
- Debugging tool failures
- Verifying tools are called in right order

---

## Common Debug Scenarios

### "Why is my message so generic?"

```yaml
output:
  show_all_variants: true  # See all 5 options
  show_prompts: true       # Check if prompt is clear
```

**Look for:**
- Are all 5 variants similar? → Increase temperature in config
- Is profile data too generic? → Improve scraper
- Is research too vague? → Check Perplexity results

---

### "Agent keeps failing/erroring"

```yaml
output:
  debug_mode: true  # See full execution
```

**Look for:**
- Which tool is failing?
- What error message?
- Is it hitting rate limits?

---

### "Why did supervisor pick THAT variant?"

```yaml
output:
  show_all_variants: true  # See all options
```

**Look at output:**
```
WHY THIS ONE (Score: 9/10):
Most specific references...

WHY NOT OTHERS:
Variant 1 too generic
Variant 2 weak CTA
```

If you disagree, adjust selection criteria in `prompts.yaml`

---

### "Is the prompt being formatted correctly?"

```yaml
output:
  show_prompts: true
```

**Check:**
- Are variables being filled in? (`{profile_data}`, `{tone}`, etc.)
- Is the prompt structure correct?
- Is context being passed?

---

### "Which tools are being called?"

```yaml
output:
  show_tool_calls: true
```

**Look for:**
- Is order correct? (scrape → research → generate → select)
- Are inputs reasonable?
- Are outputs what you expect?

---

## Combining Options

### Light Debug (Recommended for Tuning)
```yaml
output:
  verbose: true
  show_all_variants: true  # See options
  show_tool_calls: false
  show_prompts: false
  debug_mode: false
```

**Good for:** Tweaking prompts, checking message quality

---

### Medium Debug (Troubleshooting)
```yaml
output:
  verbose: true
  show_all_variants: true
  show_tool_calls: true    # See execution flow
  show_prompts: false
  debug_mode: false
```

**Good for:** Understanding why something fails, verifying tool order

---

### Full Debug (Deep Dive)
```yaml
output:
  verbose: true
  show_all_variants: true
  show_tool_calls: true
  show_prompts: true       # See prompts
  debug_mode: true         # EVERYTHING
```

**Good for:** Major issues, understanding internals

**Warning:** Generates 500+ lines of output per profile!

---

### Production (Minimal)
```yaml
output:
  verbose: true            # Just progress
  show_all_variants: false
  show_tool_calls: false
  show_prompts: false
  debug_mode: false
```

**Good for:** Batch processing, when you trust it works

---

## Performance Impact

| Option | Speed Impact | Output Size |
|--------|--------------|-------------|
| `verbose` | None | Small |
| `show_all_variants` | None | Medium (~100 lines) |
| `show_tool_calls` | None | Small (~20 lines) |
| `show_prompts` | None | Large (~200 lines) |
| `debug_mode` | Slight | HUGE (500+ lines) |

**Pro tip:** Turn off debug options for batch processing to speed up execution

---

## Quick Tips

### Save Debug Output to File
```bash
python production_simple.py > debug.log 2>&1
```

### Debug One Profile, Then Batch
```yaml
# 1. Debug single profile with all options on
output:
  debug_mode: true
  show_all_variants: true

# 2. Once working, turn off for batch
output:
  debug_mode: false
  show_all_variants: false
```

### Compare Variants Manually
```yaml
output:
  show_all_variants: true
```

Then copy all 5 variants, send to 5 different prospects, track which gets replies → use that style!

---

## Troubleshooting Debug Options

### "I set debug_mode: true but see nothing"

**Check:**
1. Did you save `config.yaml`?
2. Are you running the right script? `python production_simple.py`
3. Is it loading the right config? (should print "🐛 Debug mode enabled")

---

### "Output is overwhelming"

**Solution:** Turn off `debug_mode`, use more targeted options:
```yaml
output:
  debug_mode: false        # Turn off full debug
  show_tool_calls: true    # Just see tools
```

---

### "Variants look the same"

**Solutions:**
1. Increase temperature: `models.generator.temperature: 0.9`
2. Check if prompt is too restrictive
3. Use better model: `gpt-4o` instead of `gpt-4o-mini`

---

## TL;DR

**Normal use:**
```yaml
output:
  verbose: true
  # everything else: false
```

**Checking message quality:**
```yaml
output:
  verbose: true
  show_all_variants: true  # ← Turn this on
```

**Something's broken:**
```yaml
output:
  verbose: true
  debug_mode: true  # ← Turn this on
```

**Want to see everything:**
```yaml
output:
  verbose: true
  debug_mode: true
  show_all_variants: true
  show_prompts: true
  show_tool_calls: true
```

All controlled from `config.yaml` - no code changes! ✅
