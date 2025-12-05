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
    generate_message_variants,
    select_best_message,
    research_company
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

class EmployeeScore(BaseModel):
    """Scored employee."""
    vmid: str
    fullName: str
    title: str
    score: int = Field(ge=0, le=100)
    reasoning: str

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


# ===== SCORING LOGIC =====

def score_employees(employees: List[Employee], company_research: str) -> List[EmployeeScore]:
    """Score employees to find best targets using LLM."""

    llm = ChatOpenAI(model=CONFIG["models"]["agent"]["model"], temperature=0)

    employees_text = "\n\n".join([
        f"""EMPLOYEE {i+1}:
Name: {e.fullName}
Title: {e.title}
Summary: {e.summary[:500] if e.summary else "N/A"}
Title Description: {e.titleDescription[:500] if e.titleDescription else "N/A"}"""
        for i, e in enumerate(employees)
    ])

    prompt = f"""You are evaluating employees at a company to determine the BEST person(s) to approach for a B2B outreach campaign.

COMPANY RESEARCH:
{company_research}

EMPLOYEES:
{employees_text}

SCORING CRITERIA (0-100):
- Seniority/Decision-making power (0-30 points)
- Role relevance to our offering (0-25 points)
- Profile completeness/engagement signals (0-20 points)
- Likelihood to respond (0-25 points)

For EACH employee, provide:
1. Score (0-100)
2. Brief reasoning (2-3 sentences)

Focus on: CTOs, VPs of Digital/Tech/Marketing, Directors of key functions.
Avoid: Generic titles, incomplete profiles, junior roles.

Return as JSON array:
[
  {{"name": "Full Name", "score": 85, "reasoning": "CTO with strong digital transformation background..."}},
  ...
]"""

    result = llm.invoke([HumanMessage(content=prompt)])

    # Parse JSON response
    import json
    try:
        scores = json.loads(result.content)

        scored = []
        for emp in employees:
            match = next((s for s in scores if emp.fullName.lower() in s["name"].lower()), None)
            if match:
                scored.append(EmployeeScore(
                    vmid=emp.vmid,
                    fullName=emp.fullName,
                    title=emp.title,
                    score=match["score"],
                    reasoning=match["reasoning"]
                ))

        # Sort by score descending
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    except Exception as e:
        print(f"Error parsing scores: {e}")
        # Fallback: score by title keywords
        return fallback_scoring(employees)


def fallback_scoring(employees: List[Employee]) -> List[EmployeeScore]:
    """Fallback scoring based on title keywords."""

    scores = []
    for emp in employees:
        title_lower = emp.title.lower()

        # Simple keyword scoring
        score = 50  # Base score

        if "cto" in title_lower or "chief technology" in title_lower:
            score = 95
        elif "vp" in title_lower or "vice president" in title_lower:
            score = 90
        elif "chief" in title_lower:
            score = 85
        elif "director" in title_lower:
            score = 75
        elif "head of" in title_lower:
            score = 80
        elif "manager" in title_lower:
            score = 60

        # Bonus for digital/tech keywords
        if any(kw in title_lower for kw in ["digital", "technology", "tech", "innovation", "transformation"]):
            score += 10

        scores.append(EmployeeScore(
            vmid=emp.vmid,
            fullName=emp.fullName,
            title=emp.title,
            score=min(score, 100),
            reasoning="Scored based on title and role relevance"
        ))

    scores.sort(key=lambda x: x.score, reverse=True)
    return scores


# ===== MESSAGE GENERATION =====

def generate_message_for_employee(employee: Employee, company_research: str) -> Dict[str, Any]:
    """Generate personalized message for one employee."""

    # Build profile data
    profile_data = f"""NAME: {employee.fullName}
TITLE: {employee.title}
COMPANY: {employee.companyName}
SUMMARY: {employee.summary[:500] if employee.summary else "N/A"}
TITLE DESCRIPTION: {employee.titleDescription[:500] if employee.titleDescription else "N/A"}
LINKEDIN: {employee.linkedInProfileUrl}"""

    try:
        # Generate 5 variants
        variants = generate_message_variants(profile_data, company_research)

        # Select best
        selected = select_best_message(variants, profile_data, company_research)

        # Parse result (format: "SELECTED MESSAGE:\n{message}\n\nWHY THIS ONE...")
        message_text = selected.split("SELECTED MESSAGE:")[1].split("WHY THIS ONE")[0].strip()

        # Try to extract score
        score = 8  # Default
        if "Score:" in selected:
            try:
                score = int(selected.split("Score:")[1].split("/")[0].strip())
            except:
                pass

        return {
            "message": message_text,
            "score": score,
            "full_output": selected
        }

    except Exception as e:
        return {
            "message": "",
            "score": 0,
            "error": str(e)
        }


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
    """Process one company batch."""

    print(f"\n{'='*60}")
    print(f"Processing: {company_name} ({len(employees)} employees)")
    print(f"{'='*60}")

    # Step 1: Research company (ONCE)
    print(f"🔍 Researching {company_name}...")
    company_research = research_company(company_name, title="", context="")
    print(f"✓ Research complete")

    # Step 2: Score all employees
    print(f"📊 Scoring {len(employees)} employees...")
    scored = score_employees(employees, company_research)
    print(f"✓ Scoring complete")

    # Print scores
    for s in scored:
        print(f"  - {s.fullName} ({s.title}): {s.score}/100 - {s.reasoning[:50]}...")

    # Step 3: Select top N (configurable)
    top_n = CONFIG.get("api", {}).get("max_targets_per_company", 3)
    selected_employees = [e for e in employees if any(s.vmid == e.vmid and s.score >= 70 for s in scored[:top_n])]

    print(f"\n✅ Selected {len(selected_employees)} employees for outreach")

    # Step 4: Generate messages for selected + send to webhook
    for emp in employees:
        is_selected = any(s.vmid == emp.vmid and s.score >= 70 for s in scored[:top_n])

        result = OutreachResult(
            vmid=emp.vmid,
            fullName=emp.fullName,
            title=emp.title,
            selected=is_selected,
            selection_reasoning=""
        )

        if is_selected:
            # Find score details
            score_obj = next(s for s in scored if s.vmid == emp.vmid)
            result.selection_reasoning = f"Score: {score_obj.score}/100. {score_obj.reasoning}"

            # Generate message
            print(f"✍️  Generating message for {emp.fullName}...")
            msg_result = generate_message_for_employee(emp, company_research)

            result.message = msg_result.get("message", "")
            result.message_score = msg_result.get("score", 0)
            result.error = msg_result.get("error", "")

            print(f"✓ Message generated (score: {result.message_score}/10)")
        else:
            # Not selected
            score_obj = next((s for s in scored if s.vmid == emp.vmid), None)
            if score_obj:
                result.selection_reasoning = f"Not selected. Score: {score_obj.score}/100. {score_obj.reasoning}"
            else:
                result.selection_reasoning = "Not scored."

        # Send to webhook
        send_to_webhook(webhook_url, result)

        # Rate limiting between messages
        time.sleep(1)

    print(f"\n✅ Completed {company_name}")


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

    Expected payload:
    {
        "records": [...],  # Array of employee objects
        "numberOfResults": 6,
        "webhook_url": "https://your-webhook.com"
    }
    """

    try:
        # Log raw request for debugging
        print(f"Received request - Content-Type: {request.content_type}")
        print(f"Request data: {request.data[:500]}")  # First 500 chars

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

        if not data.get("webhook_url"):
            return jsonify({"error": "webhook_url is required"}), 400

        # Parse employees
        employees = [Employee(**record) for record in data["records"]]

        # Get company name (assume all same company)
        company_name = employees[0].companyName if employees else "Unknown"

        webhook_url = data["webhook_url"]

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
