"""
LinkedIn Outreach Agent - Production Simple with Verbalized Sampling

Features:
- All prompts in prompts.yaml (easy for non-devs to edit)
- All config in config.yaml (models, tone, CTA style)
- Verbalized Sampling for diverse, non-generic messages
- Supervisor picks best variant from 5 options
"""

import os
import yaml
import csv
import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_perplexity import ChatPerplexity
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.callbacks.base import BaseCallbackHandler
import langchain


# ===== LOAD CONFIG & PROMPTS =====

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_prompts(prompts_path: str = "prompts.yaml") -> dict:
    """Load prompts from YAML."""
    with open(prompts_path) as f:
        return yaml.safe_load(f)


# Load at module level
CONFIG = load_config()
PROMPTS = load_prompts()


# ===== DEBUG SETUP =====

# Enable LangChain debug mode if configured
if CONFIG["output"].get("debug_mode", False):
    langchain.debug = True
    print("🐛 Debug mode enabled - showing all LLM calls\n")


class DebugCallbackHandler(BaseCallbackHandler):
    """Custom callback to show agent thinking based on config."""

    def __init__(self, config: dict):
        self.config = config
        self.show_tool_calls = config["output"].get("show_tool_calls", False)
        self.show_prompts = config["output"].get("show_prompts", False)

    def on_llm_start(self, serialized, prompts, **kwargs):
        if self.show_prompts:
            model_name = serialized.get("name", "LLM")
            print(f"\n🤔 Calling {model_name}...")
            print("─" * 60)
            print("PROMPT:")
            print(prompts[0][:500] + "..." if len(prompts[0]) > 500 else prompts[0])
            print("─" * 60)

    def on_llm_end(self, response, **kwargs):
        if self.show_prompts:
            output = response.generations[0][0].text
            print(f"\n✓ Response received ({len(output)} chars)")
            if len(output) < 300:
                print("OUTPUT:", output)

    def on_tool_start(self, serialized, input_str, **kwargs):
        if self.show_tool_calls:
            tool_name = serialized.get("name", "tool")
            print(f"\n🔧 Using tool: {tool_name}")
            print(f"   Input: {input_str[:200]}..." if len(str(input_str)) > 200 else f"   Input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        if self.show_tool_calls:
            print(f"✓ Tool complete")
            if len(str(output)) < 300:
                print(f"   Output: {output}")


# ===== STRUCTURED OUTPUTS =====

class MessageVariant(BaseModel):
    """One message variant from verbalized sampling."""
    message: str
    probability: float
    profile_details_used: List[str]
    research_insights_used: List[str]
    hook_type: str


class MessageVariants(BaseModel):
    """Collection of message variants."""
    variants: List[MessageVariant]


class SelectedMessage(BaseModel):
    """The selected best message."""
    message: str
    reason: str
    rejected_reasons: str
    score: int = Field(ge=1, le=10)


# ===== MOCK SCRAPER =====

def mock_linkedin_scraper(url: str) -> Dict[str, str]:
    """Replace with real scraper API (Proxycurl, Bright Data, etc)."""
    return {
        "name": "Sarah Chen",
        "title": "VP Engineering",
        "company": "DataScale AI",
        "location": "San Francisco",
        "experience": "15+ years ML infrastructure, ex-Meta & Google",
        "recent_activity": "Posted about scaling vector DBs for RAG. Spoke at AI Infrastructure Summit 2024."
    }


# ===== TOOLS =====

@tool
def scrape_linkedin_profile(linkedin_url: str) -> str:
    """Scrape LinkedIn profile data."""
    profile = mock_linkedin_scraper(linkedin_url)
    return f"""NAME: {profile['name']}
TITLE: {profile['title']}
COMPANY: {profile['company']}
LOCATION: {profile['location']}
EXPERIENCE: {profile['experience']}
RECENT ACTIVITY: {profile['recent_activity']}"""


@tool
def research_company(company: str, title: str = "", context: str = "") -> str:
    """Research company using Perplexity."""
    perplexity = ChatPerplexity(
        model=CONFIG["models"]["research"]["model"],
        api_key=os.getenv("PERPLEXITY_API_KEY")
    )

    # Format prompt from template
    prompt_template = PROMPTS["tools"]["research_company"]
    prompt = prompt_template.format(
        company=company,
        title=title,
        context=f"Context: {context}" if context else ""
    )

    result = perplexity.invoke([HumanMessage(content=prompt)])
    return result.content


@tool
def generate_message_variants(profile_data: str, research_data: str) -> str:
    """Generate 5 diverse message variants using Verbalized Sampling."""
    llm = ChatOpenAI(
        model=CONFIG["models"]["generator"]["model"],
        temperature=CONFIG["models"]["generator"]["temperature"]
    )

    # Get rules from config
    rules = CONFIG["message_rules"]

    # Format prompt from template with verbalized sampling
    prompt_template = PROMPTS["tools"]["generate_message_variants"]
    prompt = prompt_template.format(
        profile_data=profile_data,
        research_data=research_data,
        max_words=rules["max_words"],
        tone=rules["tone"],
        cta_style=rules["cta_style"]
    )

    # Generate variants
    result = llm.invoke([HumanMessage(content=prompt)])

    # Show all variants if configured
    if CONFIG["output"].get("show_all_variants", False):
        print("\n" + "=" * 60)
        print("📝 ALL 5 VARIANTS GENERATED:")
        print("=" * 60)
        print(result.content)
        print("=" * 60 + "\n")

    # Return raw XML response for selector to parse
    return result.content


@tool
def select_best_message(variants: str, profile_data: str, research_data: str) -> str:
    """Select the best message from variants."""
    llm = ChatOpenAI(
        model=CONFIG["models"]["agent"]["model"],
        temperature=0
    )

    # Use structured output for selection
    structured_llm = llm.with_structured_output(SelectedMessage)

    # Format selector prompt
    prompt_template = PROMPTS["tools"]["select_best_message"]
    prompt = prompt_template.format(
        variants=variants,
        profile_data=profile_data,
        research_data=research_data
    )

    result = structured_llm.invoke([HumanMessage(content=prompt)])

    # Return formatted result
    return f"""SELECTED MESSAGE:
{result.message}

WHY THIS ONE (Score: {result.score}/10):
{result.reason}

WHY NOT OTHERS:
{result.rejected_reasons}"""


# ===== AGENT =====

def create_outreach_agent():
    """Create the agent with all tools."""
    llm = ChatOpenAI(
        model=CONFIG["models"]["agent"]["model"],
        temperature=CONFIG["models"]["agent"]["temperature"]
    )

    return create_agent(
        model=llm,
        tools=[
            scrape_linkedin_profile,
            research_company,
            generate_message_variants,
            select_best_message
        ],
        system_prompt=PROMPTS["supervisor"]["system"]
    )


# ===== SINGLE EXECUTION =====

def generate_outreach(linkedin_url: str, verbose: bool = None) -> Dict[str, Any]:
    """Generate outreach for a single profile."""
    if verbose is None:
        verbose = CONFIG["output"]["verbose"]

    agent = create_outreach_agent()

    if verbose:
        print(f"🔍 Processing {linkedin_url}...")

    try:
        # Setup callbacks if debug options are enabled
        callbacks = []
        if CONFIG["output"].get("show_tool_calls", False) or CONFIG["output"].get("show_prompts", False):
            callbacks.append(DebugCallbackHandler(CONFIG))

        # Invoke agent with callbacks if configured
        invoke_config = {"callbacks": callbacks} if callbacks else {}
        result = agent.invoke(
            {"messages": [{"role": "user", "content": linkedin_url}]},
            config=invoke_config
        )

        output = result["messages"][-1].content

        if verbose:
            print("✓ Success\n")

        return {
            "url": linkedin_url,
            "success": True,
            "message": output
        }

    except Exception as e:
        if verbose:
            print(f"✗ Failed: {e}\n")

        return {
            "url": linkedin_url,
            "success": False,
            "error": str(e)
        }


# ===== BATCH PROCESSING =====

def batch_outreach(
    linkedin_urls: List[str],
    output_file: str = "outreach_results.csv"
) -> List[Dict[str, Any]]:
    """Process multiple profiles with Verbalized Sampling."""

    results = []
    batch_config = CONFIG["batch"]
    delay = batch_config["delay_seconds"]
    stop_on_error = batch_config["stop_on_error"]
    incremental_save = batch_config["incremental_save"]

    print(f"🚀 Processing {len(linkedin_urls)} profiles...")
    print(f"📝 Results will be saved to {output_file}")
    print(f"⚙️  Using Verbalized Sampling (5 variants per profile)\n")
    print("=" * 60)

    for i, url in enumerate(linkedin_urls, 1):
        print(f"\n[{i}/{len(linkedin_urls)}] {url}")

        result = generate_outreach(url, verbose=True)
        results.append(result)

        # Incremental save
        if incremental_save:
            save_results(results, output_file)

        # Stop on error?
        if not result["success"] and stop_on_error:
            print(f"\n⚠️  Stopped batch due to error (stop_on_error=True)")
            break

        # Rate limiting
        if i < len(linkedin_urls) and delay > 0:
            time.sleep(delay)

    print("\n" + "=" * 60)
    print(f"✅ Batch complete! Processed {len(results)}/{len(linkedin_urls)} profiles")
    print(f"📊 Success rate: {sum(1 for r in results if r['success'])}/{len(results)}")

    # Final save
    save_results(results, output_file)

    return results


def save_results(results: List[Dict[str, Any]], output_file: str):
    """Save results to CSV."""
    with open(output_file, "w", newline="") as f:
        fieldnames = ["url", "success", "message", "error"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({
                "url": result["url"],
                "success": result["success"],
                "message": result.get("message", ""),
                "error": result.get("error", "")
            })

    print(f"💾 Saved to {output_file}")


# ===== MAIN =====

def main():
    """Demo single profile."""
    print("🎯 LinkedIn Outreach Agent (with Verbalized Sampling)")
    print("=" * 60)
    print(f"Model: {CONFIG['models']['generator']['model']}")
    print(f"Tone: {CONFIG['message_rules']['tone']}")
    print(f"CTA Style: {CONFIG['message_rules']['cta_style']}")
    print(f"Generating 5 variants per profile, selecting best")

    # Show debug options if enabled
    debug_opts = []
    if CONFIG["output"].get("debug_mode"):
        debug_opts.append("debug_mode")
    if CONFIG["output"].get("show_all_variants"):
        debug_opts.append("show_all_variants")
    if CONFIG["output"].get("show_prompts"):
        debug_opts.append("show_prompts")
    if CONFIG["output"].get("show_tool_calls"):
        debug_opts.append("show_tool_calls")

    if debug_opts:
        print(f"🐛 Debug options: {', '.join(debug_opts)}")

    print("=" * 60)

    result = generate_outreach("https://linkedin.com/in/sarah-chen")

    print("\n" + "=" * 60)
    print("🎯 FINAL RESULT:")
    print("=" * 60)
    print(result["message"])
    print("\n✅ Done!")


if __name__ == "__main__":
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set!")
        exit(1)
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  PERPLEXITY_API_KEY not set!")
        exit(1)

    # Single demo
    main()

    # Or batch mode (uncomment to use):
    # urls = [
    #     "https://linkedin.com/in/person1",
    #     "https://linkedin.com/in/person2",
    #     "https://linkedin.com/in/person3"
    # ]
    # batch_outreach(urls, output_file="results.csv")
