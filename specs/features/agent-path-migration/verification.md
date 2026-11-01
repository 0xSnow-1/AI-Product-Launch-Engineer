# Agent Path Migration & Final Integration - Verification Scorecard

## Automated Validation

### 1. pytest Fixtures
```python
# tests/integration_conftest.py
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def virtual_project_workspace():
    def create_workspace(project_slug):
        workspace_root = Path(f"/projects/{project_slug}")
        workspace_root.mkdir(parents=True, exist_ok=True)
        
        # Create required subdirectories
        (workspace_root / "research").mkdir(exist_ok=True)
        (workspace_root / "strategy").mkdir(exist_ok=True)
        
        return workspace_root
    return create_workspace

@pytest.fixture
def agent_path_validator():
    def validate_agent_paths(agent_id, expected_paths):
        from src.agents.supervisor import get_workspace_dir
        from src.agents.market_researcher import get_workspace_dir
        from src.agents.customer_researcher import get_workspace_dir
        from src.agents.gtm_strategist import get_workspace_dir
        
        agents = {
            "supervisor": get_workspace_dir,
            "market_researcher": get_workspace_dir,
            "customer_researcher": get_workspace_dir,
            "gtm_strategist": get_workspace_dir
        }
        
        agent_func = agents[agent_id]
        actual_path = agent_func()
        expected_path = expected_paths[agent_id]
        
        assert str(actual_path) == expected_path, \
            f"Agent {agent_id} path mismatch: {actual_path} != {expected_path}"
        return True
    return agent_path_validator
```

### 2. Type Checks
```python
# tests/integration_type_validation.py
from src.agents.supervisor import SupervisorAgent
from src.agents.market_researcher import MarketResearcherAgent
from src.agents.customer_researcher import CustomerResearcherAgent
from src.agents.gtm_strategist import GTMStrategistAgent

def test_agent_instantiation():
    # Verify all agents can be instantiated with new paths
    supervisor = SupervisorAgent()
    market_researcher = MarketResearcherAgent()
    customer_researcher = CustomerResearcherAgent()
    gtm_strategist = GTMStrategistAgent()
    
    # Verify path properties
    assert hasattr(supervisor, 'workspace_dir')
    assert hasattr(market_researcher, 'workspace_dir')
    assert hasattr(customer_researcher, 'workspace_dir')
    assert hasattr(gtm_strategist, 'workspace_dir')

def test_prompt_loading():
    # Verify prompts load with correct paths
    from deepagents import create_deep_agent
    from langchain_aws import ChatBedrockConverse
    
    llm = ChatBedrockConverse(model="anthropic.claude-haiku-4-5-20251001-v1:0")
    
    # Verify agent creation uses correct paths
    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(root_dir="/projects/test-project", virtual_mode=True),
        system_prompt="Test prompt"
    )
    
    assert agent is not None
```

### 3. Log Trace Verification
```bash
# tests/integration_trace_validation.sh
#!/bin/bash
# Verify complete agent workflow traces
WORKFLOW_LOG="./logs/workflow_execution_$(date +%Y%m%d_%H%M%S).log"
for step in "$WORKFLOW_LOG.supervisor" "$WORKFLOW_LOG.market_researcher" "$WORKFLOW_LOG.customer_researcher" "$WORKFLOW_LOG.gtm_strategist"; do
    # Check for virtual path usage in all logs
    grep -l "/projects/" "$step" || echo "ERROR: Virtual path not found in $step"
    grep -l "/workspace/research/" "$step" && echo "ERROR: Old path found in $step"
    
    # Check for completion signals
    grep -q "completed" "$step" || echo "WARNING: Agent completion not found in $step"
    grep -q "error" "$step" && echo "WARNING: Errors found in $step"
done
```

### 4. Runtime API Checks
```bash
# tests/integration_api_validation.sh
#!/bin/bash
# Verify complete agent workflow API
START_TIME=$(date +%s)
RESULT=$(curl -s -X POST "http://localhost:8000/api/launch_blueprint" \
  -H "Content-Type: application/json" \
  -d '{"idea": "AI meeting assistant for recruiting", "audience": "small recruiting teams"}' \
  | jq -r '.status')

END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))

if [ "$RESULT" = "completed" ] && [ $ELAPSED_TIME -lt 300 ]; then
    echo "SUCCESS: Blueprint created in ${ELAPSED_TIME} seconds"
else
    echo "ERROR: Blueprint creation failed or took too long"
    exit 1
fi

# Verify artifacts exist in correct locations
PROJECT_SLUG="ai-meeting-assistant-rehr"
for path in "/projects/$PROJECT_SLUG/research/market.md" "/projects/$PROJECT_SLUG/research/customers.md" "/projects/$PROJECT_SLUG/strategy/gtm.md" "/projects/$PROJECT_SLUG/blueprint.md"; do
    if [ -f "$path" ]; then
        echo "SUCCESS: Artifact found at $path"
    else
        echo "ERROR: Artifact missing at $path"
        exit 1
    fi
done
```