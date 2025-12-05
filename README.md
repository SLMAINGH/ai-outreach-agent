# 🎯 LinkedIn Outreach Agent - Original vs Improved

This repo contains two versions of a LinkedIn outreach automation agent:
1. **Original**: Basic tool-calling supervisor pattern
2. **Improved**: LangGraph-based workflow with best practices

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Set API Keys
```bash
export OPENAI_API_KEY="your-key"
export PERPLEXITY_API_KEY="your-key"
```

### Run Original Version
```bash
python linkedin_outreach_original.py
```

### Run Improved Version
```bash
python improved_linkedin_outreach.py
```

## 📊 Key Differences

| Feature | Original | Improved |
|---------|----------|----------|
| **Architecture** | create_agent with tools | LangGraph StateGraph |
| **State Management** | TypedDict | Pydantic Models |
| **Retry Logic** | Manual tracking | Built-in RetryPolicy |
| **Output Format** | Strings | Structured Pydantic |
| **Workflow Control** | LLM decides | Explicit nodes + edges |
| **Persistence** | None | Checkpointing |
| **Streaming** | No | Yes |
| **Error Handling** | Basic try/catch | Multi-tier strategy |
| **Quality Gates** | Tool-based reviews | Dedicated nodes |
| **Debugging** | Print statements | LangSmith + streaming |

## 🎓 What You'll Learn

The improved version demonstrates:
- ✅ **LangGraph workflows** vs basic agents
- ✅ **Supervisor pattern** with specialized nodes
- ✅ **Structured output** with Pydantic
- ✅ **Automatic retry policies** for resilience
- ✅ **Checkpointing** for long-running workflows
- ✅ **Command API** for state + routing
- ✅ **Quality gates** with conditional edges
- ✅ **Streaming execution** for real-time updates
- ✅ **Production-ready** error handling

## 📖 Documentation

See `IMPROVEMENTS.md` for detailed explanations of every improvement, backed by official LangChain docs.

## 🏗️ Architecture

### Original
```
User → Supervisor Agent → Tools → Output
```

### Improved
```
START → scrape_profile → review_profile → research_company
  → review_research → generate_message → review_message
  → finalize → END
```

Each node has:
- Single responsibility
- Retry policy
- Structured I/O
- Quality gates

## 🧪 Example Output

### Original
```
🎯 FINAL PERSONALIZED MESSAGE:
==================================================
Hey John! I noticed your recent post about vector databases...
```

### Improved
```
🚀 Starting LinkedIn Outreach Agent
============================================================

[scrape_profile] ✓ Scraped profile for Sarah Chen
[review_profile] ✓ Profile approved: Sarah Chen @ DataScale AI
[research_company] ✓ Researched DataScale AI
[review_research] ✓ Research approved
[generate_message] ✓ Generated draft message
[review_message] ✓ Message approved! High quality.
[finalize] ✅ Outreach message complete!

============================================================
🎯 FINAL PERSONALIZED MESSAGE:
============================================================
Hi Sarah! Saw your AI Infrastructure Summit talk on scaling
vector DBs for RAG—loved the bit about query optimization at
1B+ QPS. DataScale's recent $50M Series B seems timed perfectly
for the hiring push. Would love to chat about challenges in
productionizing LLM infrastructure. Coffee in SF next week?

============================================================

📊 METADATA:
Profile refs: AI Infrastructure Summit talk, vector databases, RAG
Research refs: $50M Series B funding, hiring push
Quality score: 9/10
Attempts: Profile=1, Research=1, Message=1

✅ All quality gates passed!
```

## 🛠️ Customization

### Add Real LinkedIn Scraper
Replace `mock_linkedin_scraper()` with:
- Proxycurl API
- Bright Data
- ScrapingBee
- Custom Selenium script

### Add Human Approval
```python
# In finalize_node:
if state.message_review.quality_score < 8:
    return Command(goto=END, update={"needs_approval": True})
```

### Deploy to Production
```bash
# Install LangGraph CLI
pip install langgraph-cli

# Create langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "outreach": "./improved_linkedin_outreach.py:create_outreach_graph"
  }
}

# Deploy
langgraph up
```

## 📚 Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain V1 Migration Guide](https://python.langchain.com/docs/versions/v0_2/)
- [Supervisor Pattern Tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)

## 🤝 Contributing

This is a learning project demonstrating LangChain/LangGraph best practices.
Feel free to:
- Add more examples
- Improve prompts
- Add new features
- Fix bugs

## ⚠️ Disclaimer

This is for educational purposes. Always:
- Respect LinkedIn's ToS
- Get consent before scraping
- Follow GDPR/privacy laws
- Use rate limiting
- Don't spam people

## 📝 License

MIT
