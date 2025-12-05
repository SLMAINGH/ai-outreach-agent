# 🤖 AI Outreach Agent

**LinkedIn outreach automation with Verbalized Sampling** - generates 5 diverse message variants, picks the best one.

Perfect for agencies: non-devs can edit prompts/config, no code changes needed.

---

## ✨ Features

- 🎯 **Verbalized Sampling** - Generates 5 unique variants per profile, supervisor picks best (1.6-2.1x more creative)
- 📝 **YAML Configs** - All prompts in `prompts.yaml`, all settings in `config.yaml` (non-dev friendly)
- 🔧 **Debug Options** - See all variants, prompts, tool calls via config flags
- 📊 **Batch Processing** - Process 100s of profiles, export to CSV
- 🏢 **Agency-Ready** - Different configs per client, easy A/B testing
- 🔌 **Clay Integration** - Flask API for webhooks, auto-scores employees, queues companies

---

## 🚀 Quick Start

### Standalone Mode (CLI)

1. **Install**
```bash
pip install -r requirements.txt
```

2. **Set API Keys**
```bash
export OPENAI_API_KEY="sk-..."
export PERPLEXITY_API_KEY="pplx-..."
```

3. **Run**
```bash
python main.py
```

### API Mode (Clay Integration)

1. **Deploy to Railway**
   - Connect GitHub repo
   - Set environment variables (API keys)
   - Deploy

2. **Configure Clay**
   - Add HTTP API enrichment
   - URL: `https://your-app.railway.app/process`
   - Include `webhook_url` in request body

3. **Receive Results**
   - Get scored employees + messages via webhook
   - One webhook call per employee

See **[API.md](API.md)** for full Clay integration guide

---

## 📖 Documentation

- **[API.md](API.md)** - Clay integration guide (Flask API, webhooks)
- **[QUICKSTART.md](QUICKSTART.md)** - Installation, usage, configuration
- **[DEBUG_OPTIONS.md](DEBUG_OPTIONS.md)** - See agent thinking, all 5 variants
- **[VERBALIZED_SAMPLING.md](VERBALIZED_SAMPLING.md)** - How it works, why it's better

---

## 🎯 How It Works

### 1. Scrape LinkedIn Profile
```
NAME: Sarah Chen
TITLE: VP Engineering
COMPANY: DataScale AI
RECENT ACTIVITY: Posted about scaling vector DBs for RAG
```

### 2. Research Company (Perplexity)
```
- DataScale AI raised $50M Series B (Nov 2024)
- Hiring: 10 open engineering roles
- Challenge: Scaling vector DB queries to 1B+ QPS
```

### 3. Generate 5 Variants (Verbalized Sampling)
```
Variant 1: "Hey Sarah! Saw your AI Summit talk on vector DBs..."
Variant 2: "Your post about RAG scaling hit home..."
Variant 3: "Sarah - that 1B+ QPS stat was wild..."
Variant 4: "DataScale's $50M Series B seems timed perfectly..."
Variant 5: "Your Meta experience with rec systems is impressive..."
```

### 4. Supervisor Picks Best
```
SELECTED: Variant 1 (Score: 9/10)
WHY: Most specific references (named conference, cited metric,
included funding amount). Natural tone. Clear CTA.
```

---

## ⚙️ Configuration

### Change Tone (config.yaml)
```yaml
message_rules:
  tone: "casual and friendly"  # or "professional but approachable"
  cta_style: "15-min quick call"  # or "casual coffee chat"
```

### Change Model (config.yaml)
```yaml
models:
  generator:
    model: "gpt-4o-mini"  # 10x cheaper than gpt-4o
```

### Edit Prompts (prompts.yaml)
```yaml
tools:
  generate_message_variants: |
    Generate 5 diverse messages...

    RULES:
    1. Reference 3+ profile details  # Change this!
    2. Under 75 words  # Was 100
```

**No code changes needed!** Your account manager can tweak these.

---

## 🐛 Debug Options

See what's happening under the hood:

```yaml
# config.yaml
output:
  show_all_variants: true  # See all 5 options before selection
  debug_mode: true         # Full debug (all LLM calls)
  show_tool_calls: true    # See tool execution flow
```

Full guide: **[DEBUG_OPTIONS.md](DEBUG_OPTIONS.md)**

---

## 📦 Batch Processing

```python
# Uncomment in main.py:
urls = [
    "https://linkedin.com/in/person1",
    "https://linkedin.com/in/person2",
    "https://linkedin.com/in/person3"
]
batch_outreach(urls, output_file="results.csv")
```

Output CSV:
```csv
url,success,message,error
https://linkedin.com/in/person1,True,"Hey John! Saw your post...",
https://linkedin.com/in/person2,True,"Sarah - your talk was...",
https://linkedin.com/in/person3,False,,Rate limit exceeded
```

---

## 🏗️ Tech Stack

- **LangChain v1** - Agent framework with `create_agent`
- **OpenAI GPT-4o** - Message generation (5 variants via Verbalized Sampling)
- **Perplexity Sonar** - Company research with real-time web search
- **Pydantic** - Structured outputs and validation
- **YAML** - Config management (non-dev friendly)

---

## 💰 Cost

**Per Profile (with Verbalized Sampling):**
- GPT-4o: ~$0.025 (5 variants + selection)
- GPT-4o-mini: ~$0.0025 (10x cheaper)
- Perplexity: ~$0.01

**100 profiles:** $2.50-3.50 (GPT-4o) or $0.35 (GPT-4o-mini)

---

## 🎓 Why Verbalized Sampling?

**Problem:** LLMs have "mode collapse" - always give the most generic response.

**Solution:** Generate 5 diverse variants from "tail of distribution" (low-probability, creative options), then pick best.

**Result:** 1.6-2.1x more creative outputs while maintaining quality ([source](https://www.verbalized-sampling.com))

### Example Output
```
SELECTED MESSAGE:
Hey Sarah! Saw your AI Infrastructure Summit talk on scaling
vector DBs—the query optimization for 1B+ QPS was mind-blowing.
DataScale's $50M Series B seems perfectly timed for your hiring
push. Coffee in SF to chat about productionizing LLM infrastructure?

WHY THIS ONE (Score: 9/10):
Most specific references (conference name, exact metric, funding
amount with date). Natural peer-to-peer tone. Strong hook with
1B+ QPS stat. Clear, casual CTA.

WHY NOT OTHERS:
Variant 1: too generic (just mentioned "ML experience")
Variant 2: weak CTA ("let me know if interested")
Variant 3: too formal ("I hope this finds you well")
Variant 4: too sales-y ("explore synergies")
```

---

## 🏢 Perfect for Agencies

### Client A: Tech Startups
```yaml
# config_techcorp.yaml
message_rules:
  tone: "casual and friendly"
  cta_style: "casual coffee chat"
  max_words: 80
```

### Client B: Enterprise/Finance
```yaml
# config_finance.yaml
message_rules:
  tone: "professional but approachable"
  cta_style: "15-min scheduled call"
  max_words: 100
```

Load different configs:
```python
CONFIG = load_config("config_techcorp.yaml")
```

---

## 📁 Project Structure

```
├── main.py                   # Main agent code (370 lines)
├── config.yaml              # All settings (models, tone, batch)
├── prompts.yaml             # All prompts (with examples)
├── requirements.txt         # Dependencies
├── README.md               # This file
├── QUICKSTART.md           # Detailed usage guide
├── DEBUG_OPTIONS.md        # Debug configuration guide
└── VERBALIZED_SAMPLING.md  # Deep dive on technique
```

---

## 🚢 Deployment

### Railway / Heroku / Cloud Run
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...

# Run
python main.py
```

---

## 🛠️ Customization

### Add New Tool
```python
@tool
def search_crunchbase(company: str) -> str:
    """Get funding data from Crunchbase."""
    # Your implementation
    return data

# Add to agent in main.py:
tools=[..., search_crunchbase]
```

### Add New Prompt Template
```yaml
# prompts.yaml
tools:
  your_new_tool: |
    Your prompt here with {variables}
```

### Change Variant Count
```yaml
# prompts.yaml - generate 3 instead of 5
generate_message_variants: |
  Generate 3 different messages...  # Was 5
```

---

## ⚠️ Important Notes

- Replace `mock_linkedin_scraper()` with real API (Proxycurl, Bright Data, etc.)
- Respect LinkedIn's ToS - always get consent before scraping
- Use rate limiting (`batch.delay_seconds` in config)
- Don't commit API keys (they're in `.gitignore`)

---

## 🤝 Contributing

This is a production-ready template. Feel free to:
- Fork and customize for your use case
- Add new tools (email scraper, CRM integration, etc.)
- Improve prompts in `prompts.yaml`
- Add new debug options in `config.yaml`

---

## 📄 License

MIT

---

## 🔗 Resources

- [Verbalized Sampling Paper](https://www.verbalized-sampling.com)
- [LangChain Documentation](https://python.langchain.com)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Perplexity API Docs](https://docs.perplexity.ai)

---

**Built for agencies that need personalized outreach at scale** 🚀

Non-devs can edit prompts. Devs can extend functionality. Everyone wins.
