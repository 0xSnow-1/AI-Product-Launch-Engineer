# Agent Path Migration & Final Integration - Implementation Plan

## Group 1: Supervisor Agent Updates
1. **Update supervisor.py**
   - Fix WORKSPACE_DIR to use virtual path schema
   - Update blueprint assembly logic
   - Add virtual path validation middleware
   - Fix prompt loading to use correct paths
   - Implement artifact retrieval from virtual paths
   - Add blueprint validation before packaging

2. **Update supervisor/v3.yaml**
   - Fix evaluation_status to "evaluated"
   - Update instructions to use virtual paths
   - Add output contract for blueprint assembly
   - Include path validation requirements

## Group 2: Subagent Market Researcher
1. **Update market_researcher.py**
   - Fix WORKSPACE_DIR to use `/projects/{project_slug}/research/`
   - Update prompt directory path
   - Fix output contract to `/projects/{project_slug}/research/market.md`
   - Add source validation for market research
   - Implement virtual path verification middleware

2. **Update market_researcher/v1.yaml**
   - Fix evaluation_status to "evaluated"
   - Update output contract to virtual path
   - Add virtual path validation requirements
   - Include path schema documentation

## Group 3: Subagent Customer Researcher
1. **Update customer_researcher.py**
   - Fix WORKSPACE_DIR to use `/projects/{project_slug}/research/`
   - Update prompt directory path
   - Fix output contract to `/projects/{project_slug}/research/customers.md`
   - Add customer persona validation
   - Implement virtual path verification middleware

2. **Update customer_researcher/v1.yaml**
   - Fix evaluation_status to "evaluated"
   - Update output contract to virtual path
   - Add virtual path validation requirements
   - Include path schema documentation

## Group 4: Subagent GTM Strategist
1. **Update gtm_strategist.py**
   - Fix WORKSPACE_DIR to use `/projects/{project_slug}/strategy/`
   - Update prompt directory path
   - Fix output contract to `/projects/{project_slug}/strategy/gtm.md`
   - Add GTM strategy validation
   - Implement virtual path verification middleware

2. **Update gtm_strategist/v1.yaml**
   - Fix evaluation_status to "evaluated"
   - Update output contract to virtual path
   - Add virtual path validation requirements
   - Include path schema documentation

## Group 5: Integration & Workflow Updates
1. **Update prompt configurations**
   - Ensure all prompt directories use correct paths
   - Update prompt loading mechanisms
   - Add virtual path validation in agent initialization

2. **Create integration middleware**
   - Add virtual path validation layer
   - Implement artifact consistency checks
   - Add blueprint assembly verification
   - Create error recovery mechanisms

3. **Update agent coordination**
   - Fix task delegation paths
   - Update artifact sharing mechanisms
   - Add virtual path verification in handoffs

## Group 6: Testing & Validation
1. **Create comprehensive tests**
   - Unit tests for path validation
   - Integration tests for agent workflows
   - End-to-end tests for complete blueprints
   - Performance tests for agent execution

2. **Set up CI/CD pipeline**
   - Automated testing on every PR
   - Smoke gate for path validation
   - Integration testing for full workflows
   - Performance regression detection

3. **Create documentation**
   - Agent configuration guides
   - Path schema documentation
   - Troubleshooting runbook
   - Deployment procedures
