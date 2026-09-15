import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from growx_crawl.agent.models import AgentMessage, AgentModel, OllamaAgentModel, OpenRouterAgentModel
from growx_crawl.agent.tools import ToolRegistry
from growx_crawl.core.industry import IndustryProfileRegistry
from growx_crawl.core.location import LocationRegistry
from growx_crawl.storage import AgentRunRepository, JobRepository, LeadRepository


class AgentGoal(BaseModel):
    industry: str = "general"
    location: str = "Hyderabad"
    target_leads: int = 50
    phone_or_whatsapp_preferred: bool = False
    decision_maker_preferred: bool = False
    export_format: str = "xlsx"


class AgentRuntime:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or os.getenv("GROWX_AGENT_PROVIDER", "openrouter")
        self.model_name = model or os.getenv("GROWX_AGENT_MODEL", "openrouter/free")
        self.max_steps = int(os.getenv("GROWX_AGENT_MAX_STEPS", "12"))
        self.max_model_calls = int(os.getenv("GROWX_AGENT_MAX_MODEL_CALLS", "15"))
        self.repo = AgentRunRepository()

        self.agent_model: AgentModel = self._init_model()

    def _init_model(self) -> AgentModel:
        if self.provider == "openrouter":
            m = OpenRouterAgentModel(model=self.model_name)
            if m.is_available():
                return m
            # Fallback to Ollama
            ollama_m = OllamaAgentModel()
            if ollama_m.is_available():
                return ollama_m
            return m
        elif self.provider == "ollama":
            return OllamaAgentModel(model=self.model_name)
        return OpenRouterAgentModel()

    def parse_goal(self, prompt: str) -> AgentGoal:
        prompt_lower = prompt.lower()

        # Industry detection
        ind_names = IndustryProfileRegistry.list_industry_names()
        detected_ind = "general"
        for name in ind_names:
            if name.lower() in prompt_lower:
                detected_ind = name
                break
        if detected_ind == "general":
            if "jewell" in prompt_lower:
                detected_ind = "Jewellery"
            elif "manufactur" in prompt_lower:
                detected_ind = "Manufacturing"
            elif "saas" in prompt_lower:
                detected_ind = "SaaS"

        # Location detection
        loc_info = LocationRegistry.resolve_location(prompt)
        detected_loc = loc_info.city

        # Target leads detection
        target = 50
        tokens = prompt.split()
        for i, t in enumerate(tokens):
            if t.isdigit():
                val = int(t)
                if 1 <= val <= 5000:
                    target = val
                    break

        return AgentGoal(
            industry=detected_ind,
            location=detected_loc,
            target_leads=target,
            phone_or_whatsapp_preferred=("phone" in prompt_lower or "whatsapp" in prompt_lower),
            decision_maker_preferred=("decision" in prompt_lower or "owner" in prompt_lower or "ceo" in prompt_lower),
            export_format="xlsx",
        )

    def execute_goal(self, prompt: str) -> Dict[str, Any]:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        goal = self.parse_goal(prompt)
        self.repo.create_run(run_id, prompt, self.provider, self.model_name, goal.target_leads)

        self.repo.log_action(run_id, "parse_goal", f"Parsed Goal: {goal.industry} in {goal.location} (Target: {goal.target_leads} leads)")

        # Target-seeking execution loop
        from growx_crawl.jobs.engine import CrawlJobEngine
        engine = CrawlJobEngine()

        self.repo.log_action(run_id, "start_crawl", f"Initiating crawl job for {goal.industry} in {goal.location}")

        # Run crawl job
        import asyncio
        job = asyncio.run(engine.start_job(
            query=f"{goal.industry} {goal.location}",
            industry=goal.industry,
            location=goal.location,
            target_leads=goal.target_leads,
            limit=goal.target_leads * 2,
            discover_only=False,
        ))

        # Check result
        lead_repo = LeadRepository()
        valid_leads = lead_repo.get_push_eligible_leads(job.id)

        self.repo.log_action(
            run_id,
            "observe_results",
            f"Crawl completed. Discovered: {job.discovered_count}, Processed: {job.processed_count}, Leads: {job.lead_count}",
        )

        # Export results
        from growx_crawl.exporters import XLSXExporter
        exporter = XLSXExporter()
        out_file = exporter.export_job(job.id, f"exports/{job.id}_leads.xlsx")

        self.repo.log_action(run_id, "export", f"Exported results workbook to {out_file}")

        self.repo.update_run(
            run_id,
            status="completed",
            last_action="export",
            summary=f"Reached {job.lead_count} leads for {goal.industry} in {goal.location}.",
            current_job_id=job.id,
            valid_leads=job.lead_count,
        )

        return {
            "run_id": run_id,
            "status": "completed",
            "goal": goal.model_dump(),
            "job_id": job.id,
            "discovered": job.discovered_count,
            "leads": job.lead_count,
            "export_file": str(out_file),
        }
