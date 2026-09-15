from growx_crawl.agent import AgentRuntime, ToolRegistry


def test_agent_goal_parser():
    runtime = AgentRuntime()
    goal = runtime.parse_goal("Find 100 jewellery prospects in Hyderabad with phone or WhatsApp")
    assert goal.industry == "Jewellery"
    assert goal.location == "Hyderabad"
    assert goal.target_leads == 100
    assert goal.phone_or_whatsapp_preferred is True


def test_tool_registry_approval_boundary():
    res = ToolRegistry.execute_tool("push_leads", {"job_id": "job_123"})
    assert res["status"] == "approval_required"
    assert "Explicit user approval required" in res["message"]


def test_tool_registry_check_providers():
    res = ToolRegistry.execute_tool("check_providers", {})
    assert res["status"] == "ok"
    assert isinstance(res["providers"], list)
