"""
Flask API for Clay Integration
Accepts employee lists, finds best targets, generates messages, sends to webhook.
"""

import os
import yaml
import time
import requests
from typing import List, Dict, Any
from flask import Flask, request, jsonify
from queue import Queue
from threading import Thread
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_perplexity import ChatPerplexity
from langchain_core.messages import HumanMessage
import langchain

# Import from main.py
from main import (
    load_config,
    load_prompts,
    create_batch_agent
)


# ===== LOAD CONFIG =====

CONFIG = load_config()
PROMPTS = load_prompts()

# Enable debug if configured
if CONFIG["output"].get("debug_mode", False):
    langchain.debug = True


# ===== MODELS =====

class Employee(BaseModel):
    """Employee from Clay."""
    vmid: str
    title: str
    fullName: str
    firstName: str = ""
    lastName: str = ""
    summary: str = ""
    titleDescription: str = ""
    linkedInProfileUrl: str = ""
    companyName: str = ""

class ClayRequest(BaseModel):
    """Request from Clay."""
    records: List[Dict[str, Any]]
    numberOfResults: int
    webhook_url: str = Field(..., description="Where to send results")

class OutreachResult(BaseModel):
    """Result to send to webhook."""
    vmid: str
    fullName: str
    title: str
    selected: bool
    selection_reasoning: str = ""
    message: str = ""
    message_score: int = 0
    error: str = ""


# ===== FLASK APP =====

app = Flask(__name__)

# In-memory queue for processing companies
company_queue = Queue()


# ===== WEBHOOK SENDER =====

def send_to_webhook(webhook_url: str, result: OutreachResult):
    """Send result to Clay webhook."""
    try:
        response = requests.post(
            webhook_url,
            json=result.model_dump(),
            timeout=30
        )
        response.raise_for_status()
        print(f"✓ Sent to webhook: {result.fullName}")
    except Exception as e:
        print(f"✗ Webhook failed for {result.fullName}: {e}")


# ===== BATCH PROCESSOR =====

def process_company_batch(company_name: str, employees: List[Employee], webhook_url: str):
    """Process one company batch using the batch agent."""

    print(f"\n{'='*60}")
    print(f"Processing: {company_name} ({len(employees)} employees)")
    print(f"{'='*60}")

    # Convert employees to JSON for agent
    import json
    employees_data = [emp.model_dump() for emp in employees]
    employees_json = json.dumps(employees_data, indent=2)

    # Create batch agent
    print(f"🤖 Creating batch agent...")
    agent = create_batch_agent()

    # Task prompt for agent
    top_n = CONFIG.get("api", {}).get("max_targets_per_company", 3)
    task = f"""Process these employees from {company_name}.

EMPLOYEES DATA:
{employees_json}

YOUR TASK:
1. Research {company_name} (once)
2. Score all {len(employees)} employees and select top {top_n}
3. Generate personalized messages for selected employees (score >= 70)
4. Return results for ALL employees in this JSON format:
[
  {{
    "vmid": "...",
    "fullName": "...",
    "title": "...",
    "selected": true/false,
    "selection_reasoning": "Score: X/100. Reason...",
    "message": "personalized message" (only if selected),
    "message_score": 8 (only if selected),
    "error": "" (if any)
  }},
  ...
]

Remember: Research company ONCE, not per employee. Be efficient."""

    try:
        # Invoke agent with verbose output
        print(f"🚀 Agent processing...")
        print(f"   Step 1: Agent will research {company_name}")
        print(f"   Step 2: Agent will score {len(employees)} employees")
        print(f"   Step 3: Agent will generate messages for top {top_n}")
        print()

        result = agent.invoke({"messages": [{"role": "user", "content": task}]})

        # Get agent's response
        agent_output = result["messages"][-1].content
        print(f"\n✓ Agent completed")
        print(f"\n{'='*60}")
        print(f"AGENT FULL OUTPUT:")
        print(f"{'='*60}")
        print(agent_output)
        print(f"{'='*60}\n")

        # Parse JSON response
        try:
            # Extract JSON from agent output (might have extra text)
            import re
            json_match = re.search(r'\[.*\]', agent_output, re.DOTALL)
            if json_match:
                results_json = json_match.group(0)
                results = json.loads(results_json)
            else:
                raise ValueError("No JSON array found in agent output")

            # Send each result to webhook
            print(f"\n📤 Sending {len(results)} results to webhook...")
            for res in results:
                result_obj = OutreachResult(**res)
                send_to_webhook(webhook_url, result_obj)
                time.sleep(0.5)  # Small delay between webhooks

            print(f"\n✅ Completed {company_name}")

        except Exception as parse_error:
            print(f"❌ Failed to parse agent output: {parse_error}")
            print(f"Raw output: {agent_output}")

            # Send error results for all employees
            for emp in employees:
                error_result = OutreachResult(
                    vmid=emp.vmid,
                    fullName=emp.fullName,
                    title=emp.title,
                    selected=False,
                    selection_reasoning="",
                    error=f"Agent output parse error: {str(parse_error)}"
                )
                send_to_webhook(webhook_url, error_result)

    except Exception as e:
        print(f"❌ Agent error: {e}")
        import traceback
        traceback.print_exc()

        # Send error results for all employees
        for emp in employees:
            error_result = OutreachResult(
                vmid=emp.vmid,
                fullName=emp.fullName,
                title=emp.title,
                selected=False,
                selection_reasoning="",
                error=f"Agent error: {str(e)}"
            )
            send_to_webhook(webhook_url, error_result)


# ===== QUEUE WORKER =====

def queue_worker():
    """Background worker that processes company batches from queue."""
    while True:
        try:
            # Get next batch
            batch = company_queue.get()

            if batch is None:  # Shutdown signal
                break

            company_name, employees, webhook_url = batch

            # Process batch
            process_company_batch(company_name, employees, webhook_url)

            # Mark as done
            company_queue.task_done()

            # Delay between companies to avoid rate limits
            delay = CONFIG.get("api", {}).get("delay_between_companies", 5)
            print(f"\n⏳ Waiting {delay}s before next company...")
            time.sleep(delay)

        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            import traceback
            traceback.print_exc()


# Start background worker
worker_thread = Thread(target=queue_worker, daemon=True)
worker_thread.start()


# ===== API ENDPOINTS =====

@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "queue_size": company_queue.qsize()
    })


@app.route("/process", methods=["POST"])
def process_clay_webhook():
    """
    Main endpoint for Clay webhooks.

    Expected:
    - Header: X-Webhook-URL with callback URL
    - Body: The full lookup result from Clay (with records and numberOfResults)
    """

    try:
        # Log raw request for debugging
        print(f"Received request - Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Request data: {request.data[:500]}")  # First 500 chars

        # Get webhook URL from header
        webhook_url = request.headers.get("X-Webhook-URL") or request.headers.get("Webhook-URL")

        if not webhook_url:
            return jsonify({"error": "X-Webhook-URL header is required"}), 400

        # Handle both application/json and other content types
        if request.is_json:
            data = request.json
        else:
            data = request.get_json(force=True)

        print(f"Parsed data keys: {data.keys() if data else 'None'}")

        # Validate
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        if not data.get("records"):
            return jsonify({"error": "No records provided"}), 400

        # Parse employees
        employees = [Employee(**record) for record in data["records"]]

        # Get company name (assume all same company)
        company_name = employees[0].companyName if employees else "Unknown"

        # Add to queue
        company_queue.put((company_name, employees, webhook_url))

        queue_position = company_queue.qsize()

        print(f"✓ Added {company_name} to queue (position: {queue_position})")

        return jsonify({
            "status": "queued",
            "company": company_name,
            "employees": len(employees),
            "queue_position": queue_position,
            "message": f"Processing {len(employees)} employees from {company_name}. Results will be sent to webhook."
        }), 202  # 202 Accepted

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    """Root endpoint."""
    return jsonify({
        "name": "AI Outreach Agent API",
        "version": "1.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/process": "POST - Process Clay webhook"
        },
        "queue_size": company_queue.qsize()
    })


# ===== MAIN =====

if __name__ == "__main__":
    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set!")
        exit(1)
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  PERPLEXITY_API_KEY not set!")
        exit(1)

    print("🚀 Starting AI Outreach Agent API")
    print(f"Queue worker: Active")
    print(f"Max targets per company: {CONFIG.get('api', {}).get('max_targets_per_company', 3)}")
    print(f"Delay between companies: {CONFIG.get('api', {}).get('delay_between_companies', 5)}s")

    # Run Flask
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
