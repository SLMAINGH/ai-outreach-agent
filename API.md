# 🔌 API Documentation - Clay Integration

Flask API for processing Clay employee lists, scoring targets, and generating personalized outreach messages.

---

## 🚀 Quick Start

### Deploy to Railway

1. Push this repo to GitHub
2. Connect to Railway
3. Set environment variables:
   - `OPENAI_API_KEY`
   - `PERPLEXITY_API_KEY`
4. Deploy!

Railway will use `Procfile` to start the API with gunicorn.

---

## 📡 Endpoints

### `GET /`
Root endpoint with API info.

**Response:**
```json
{
  "name": "AI Outreach Agent API",
  "version": "1.0",
  "endpoints": {
    "/health": "GET - Health check",
    "/process": "POST - Process Clay webhook"
  },
  "queue_size": 0
}
```

---

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "queue_size": 0
}
```

---

### `POST /process`
Main endpoint for Clay webhooks.

**Request Body:**
```json
{
  "records": [
    {
      "vmid": "ACwAADStBdoBTipHfmeOxYKxt1Pgql9Hoi_xKL0",
      "title": "Chief Technology Officer",
      "fullName": "Mark Otieno",
      "firstName": "Mark",
      "lastName": "Otieno",
      "summary": "CTO with 15+ years experience...",
      "titleDescription": "Strategic leadership in tech...",
      "linkedInProfileUrl": "https://www.linkedin.com/in/...",
      "companyName": "Levi Strauss & Co."
    },
    ...
  ],
  "numberOfResults": 6,
  "webhook_url": "https://your-webhook-url.com/callback"
}
```

**Required Fields:**
- `records` - Array of employee objects
- `webhook_url` - Where to send results

**Response (202 Accepted):**
```json
{
  "status": "queued",
  "company": "Levi Strauss & Co.",
  "employees": 6,
  "queue_position": 1,
  "message": "Processing 6 employees from Levi Strauss & Co. Results will be sent to webhook."
}
```

---

## 🔄 How It Works

### 1. Request Received
Clay sends employee list to `/process` endpoint.

### 2. Queued for Processing
Added to queue to avoid rate limits. Multiple companies processed sequentially.

### 3. Company Research
Research company once using Perplexity:
- Recent funding/news
- Digital transformation initiatives
- Tech challenges
- Hiring trends

### 4. Employee Scoring
Score each employee (0-100) based on:
- **Seniority** (30 points) - Decision-making power
- **Role Relevance** (25 points) - How relevant to offering
- **Profile Quality** (20 points) - Completeness, engagement
- **Response Likelihood** (25 points) - Will they respond?

### 5. Select Top Targets
Pick top N employees (default: 3) with score >= 70.

### 6. Generate Messages
For selected employees:
- Generate 5 message variants (Verbalized Sampling)
- Supervisor picks best variant
- Score message quality (1-10)

### 7. Send to Webhook
For EACH employee (selected or not), send result to webhook_url.

---

## 📤 Webhook Response Format

For each employee, the API sends a POST request to your `webhook_url`:

```json
{
  "vmid": "ACwAADStBdoBTipHfmeOxYKxt1Pgql9Hoi_xKL0",
  "fullName": "Mark Otieno",
  "title": "Chief Technology Officer",
  "selected": true,
  "selection_reasoning": "Score: 95/100. CTO with strong digital transformation background and decision-making authority. Profile shows engagement with tech innovation topics.",
  "message": "Hey Mark! Saw your work transforming Levi's tech stack over the past 15 years. The security ops framework you built is impressive. Would love to chat about how we're helping CTOs scale infrastructure without the usual bottlenecks. Coffee next week?",
  "message_score": 9,
  "error": ""
}
```

**Fields:**
- `vmid` - Employee ID from Clay
- `fullName` - Full name
- `title` - Job title
- `selected` (boolean) - Was this person selected for outreach?
- `selection_reasoning` - Why they were/weren't selected
- `message` - Personalized message (empty if not selected)
- `message_score` - Quality score 1-10 (0 if not selected)
- `error` - Error message if generation failed

---

## 🎯 Clay Integration

### Step 1: Create HTTP API Enrichment

In Clay:
1. Add "HTTP API" enrichment
2. Set URL to your Railway deployment: `https://your-app.railway.app/process`
3. Method: POST
4. Headers:
   ```
   Content-Type: application/json
   ```

### Step 2: Configure Request Body

Map Clay columns to request format:

```javascript
{
  "records": {{employees_array}},  // Your employee data
  "numberOfResults": {{count}},
  "webhook_url": "{{your_webhook_url}}"  // Where to receive results
}
```

### Step 3: Set Up Webhook Receiver

Create webhook endpoint in Clay/Zapier/n8n to receive results:
- Receives one POST per employee
- Check `selected` field
- Use `message` for selected employees
- Store in Clay table

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
api:
  # How many employees to select per company
  max_targets_per_company: 3  # Top 3 by score

  # Minimum score to be selected (0-100)
  min_score_threshold: 70  # Must score >= 70

  # Delay between processing companies (seconds)
  delay_between_companies: 5  # Avoid rate limits

  # Delay between webhook calls (seconds)
  delay_between_webhooks: 1
```

---

## 📊 Processing Flow

```
Clay → POST /process
  ↓
Queue (Company 1)
  ↓
Research Company (Perplexity)
  ↓
Score 6 Employees (GPT-4o)
  ↓
Select Top 3 (score >= 70)
  ↓
Generate Messages (5 variants each)
  ↓
Send 6 Webhooks (1 per employee)
  ↓
Queue (Company 2)
  ↓
...
```

**Timing Example (6 employees):**
- Research company: 10s
- Score employees: 5s
- Generate 3 messages: 30s (10s each)
- Send 6 webhooks: 6s
- **Total: ~51s per company**

---

## 🔍 Example Workflow

### Input (from Clay)
```json
{
  "records": [
    {"fullName": "Sarah Chen", "title": "CTO", "companyName": "TechCorp", ...},
    {"fullName": "John Doe", "title": "VP Engineering", ...},
    {"fullName": "Jane Smith", "title": "Director of IT", ...},
    {"fullName": "Bob Johnson", "title": "Senior Engineer", ...},
    {"fullName": "Alice Brown", "title": "Engineering Manager", ...},
    {"fullName": "Tom Wilson", "title": "DevOps Lead", ...}
  ],
  "webhook_url": "https://hooks.clay.com/callback/abc123"
}
```

### Processing
1. **Research TechCorp** - "Raised $50M Series B, hiring for cloud migration..."
2. **Score employees:**
   - Sarah Chen (CTO): 95/100 ✅ SELECTED
   - John Doe (VP): 90/100 ✅ SELECTED
   - Jane Smith (Director): 75/100 ✅ SELECTED
   - Bob Johnson (Senior): 55/100 ❌ Not selected
   - Alice Brown (Manager): 65/100 ❌ Below threshold
   - Tom Wilson (Lead): 68/100 ❌ Below threshold

3. **Generate messages** for top 3
4. **Send 6 webhooks** (all employees, with selected flag)

### Output (6 webhook calls)

**Webhook 1 (Sarah - SELECTED):**
```json
{
  "vmid": "...",
  "fullName": "Sarah Chen",
  "title": "CTO",
  "selected": true,
  "selection_reasoning": "Score: 95/100. CTO with decision-making authority...",
  "message": "Hey Sarah! Saw TechCorp's $50M Series B announcement...",
  "message_score": 9,
  "error": ""
}
```

**Webhook 4 (Bob - NOT SELECTED):**
```json
{
  "vmid": "...",
  "fullName": "Bob Johnson",
  "title": "Senior Engineer",
  "selected": false,
  "selection_reasoning": "Not selected. Score: 55/100. Senior role but lacks decision-making authority for this outreach.",
  "message": "",
  "message_score": 0,
  "error": ""
}
```

---

## 🚦 Rate Limiting

**Built-in queue system** prevents rate limit issues:

1. **Sequential Company Processing** - One company at a time
2. **Configurable Delays** - Wait between companies (`delay_between_companies`)
3. **Webhook Throttling** - Pause between webhook calls

**Config:**
```yaml
api:
  delay_between_companies: 5  # 5s between companies
  delay_between_webhooks: 1   # 1s between webhook calls
```

**Multiple Requests:**
If Clay sends 10 companies:
- All queued immediately (returns 202 Accepted)
- Processed sequentially with delays
- No rate limit issues

---

## 🐛 Debugging

### Check Queue Status
```bash
curl https://your-app.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "queue_size": 3  # 3 companies waiting
}
```

### View Logs (Railway)
Railway dashboard → Logs → See real-time processing

```
✓ Added Levi Strauss & Co. to queue (position: 1)
============================================================
Processing: Levi Strauss & Co. (6 employees)
============================================================
🔍 Researching Levi Strauss & Co....
✓ Research complete
📊 Scoring 6 employees...
✓ Scoring complete
  - Mark Otieno (CTO): 95/100 - Strong technical leadership...
  - Robin Hoffmann (CTO): 90/100 - Digital transformation focus...
  ...
✅ Selected 3 employees for outreach
✍️  Generating message for Mark Otieno...
✓ Message generated (score: 9/10)
✓ Sent to webhook: Mark Otieno
...
✅ Completed Levi Strauss & Co.
⏳ Waiting 5s before next company...
```

---

## ⚠️ Error Handling

### Webhook Fails
If webhook URL is unreachable:
- Error logged
- Processing continues
- Check logs for failed webhooks

### LLM Fails
If message generation fails:
- Employee still sent to webhook
- `error` field populated
- `message` is empty
- `selected` stays true

### API Fails
If entire batch fails:
- Error logged
- Queue continues with next company
- Check `/health` for queue status

---

## 💰 Cost Estimates

**Per Company (6 employees, 3 selected):**
- Company research (Perplexity): $0.01
- Scoring (GPT-4o): $0.005
- Message generation (GPT-4o, 3 × 5 variants): $0.075
- **Total: ~$0.09 per company**

**Using GPT-4o-mini:**
- Message generation: $0.0075
- **Total: ~$0.02 per company** (4x cheaper!)

**100 companies:** $9 (GPT-4o) or $2 (GPT-4o-mini)

---

## 🔒 Security

- ✅ No data stored (stateless API)
- ✅ Environment variables for API keys
- ✅ HTTPS only (Railway enforces)
- ✅ No authentication needed (deploy is private URL)
- ⚠️ Add auth if exposing publicly

---

## 🚀 Deployment Checklist

- [ ] Push code to GitHub
- [ ] Connect repo to Railway
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Set `PERPLEXITY_API_KEY` environment variable
- [ ] Deploy
- [ ] Test with `/health` endpoint
- [ ] Test with sample POST to `/process`
- [ ] Configure Clay HTTP API enrichment
- [ ] Set up webhook receiver in Clay
- [ ] Run test batch

---

## 📞 Testing

### Local Test
```bash
# Start API locally
python api.py

# Test in another terminal
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "vmid": "test123",
        "title": "CTO",
        "fullName": "Test User",
        "companyName": "Test Corp",
        "summary": "Experienced CTO...",
        "linkedInProfileUrl": "https://linkedin.com/in/test"
      }
    ],
    "webhook_url": "https://webhook.site/your-unique-url"
  }'
```

Use [webhook.site](https://webhook.site) to see responses!

---

## 🎯 Best Practices

1. **Test with webhook.site first** - See responses before Clay integration
2. **Start with 1 company** - Make sure it works
3. **Monitor costs** - Check OpenAI usage dashboard
4. **Tune scoring thresholds** - Adjust `min_score_threshold` based on results
5. **Review selected employees** - Are they the right targets?
6. **A/B test message quality** - Try different prompts in `prompts.yaml`

---

## TL;DR

1. Deploy to Railway with API keys
2. Clay sends employee list to `/process`
3. API researches company, scores employees, picks top 3
4. Generates personalized messages for selected
5. Sends results to your webhook (one call per employee)
6. Queue system handles multiple companies sequentially

**Your Railway URL:** `https://your-app.railway.app`

**Clay HTTP API Enrichment:**
- URL: `https://your-app.railway.app/process`
- Method: POST
- Body: Include `records` and `webhook_url`
