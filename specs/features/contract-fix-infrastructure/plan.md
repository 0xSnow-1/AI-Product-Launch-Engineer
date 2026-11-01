# Contract Fix & Infrastructure Setup - Implementation Plan

## Group 1: Path Contract Migration
**Tasks:** (Sequential - Group 1 → 2 → 3)

1. **Update Supervisor Agent**
   - Fix WORKSPACE_DIR path in supervisor.py
   - Update prompt references to use virtual paths
   - Add blueprint assembly using new virtual scheme

2. **Update Subagent Market Researcher**
   - Fix `/workspace/research/competitors.md` → `/projects/{project_slug}/research/market.md`
   - Update prompt output contract
   - Add source citation validation

3. **Update Subagent Customer Researcher**
   - Fix `/workspace/research/customers.md` → `/projects/{project_slug}/research/customers.md`
   - Update prompt output contract
   - Add customer persona validation

4. **Update Subagent GTM Strategist**
   - Fix `/workspace/research/gtm_strategy.md` → `/projects/{project_slug}/strategy/gtm.md`
   - Update prompt output contract
   - Add GTM strategy validation

## Group 2: Prompt System Updates
1. **Update Supervisor Prompt**
   - Update v3.yaml evaluation_status to "evaluated"
   - Add output contract for blueprint assembly
   - Include virtual path instructions

2. **Update Market Researcher Prompt**
   - Update v1.yaml evaluation_status to "evaluated"
   - Fix output contract to use `/projects/{project_slug}/research/market.md`
   - Add virtual path validation instructions

3. **Update Customer Researcher Prompt**
   - Update v1.yaml evaluation_status to "evaluated"
   - Fix output contract to use `/projects/{project_slug}/research/customers.md`
   - Add virtual path validation instructions

4. **Update GTM Strategist Prompt**
   - Update v1.yaml evaluation_status to "evaluated"
   - Fix output contract to use `/projects/{project_slug}/strategy/gtm.md`
   - Add virtual path validation instructions

## Group 3: Evaluation Infrastructure
1. **Create evals/spec.md**
   - Define input/output schemas
   - Document artifact paths and formats
   - Specify hard gates and scored dimensions
   - Include task examples and reference outputs

2. **Implement evals/run_evals.py**
   - Create trial isolation mechanism
   - Add workspace sandboxing
   - Implement artifact capture and grading
   - Add transcript recording for debugging

3. **Implement evals/evaluators.py**
   - Create artifact_exists grader
   - Implement section_coverage grader
   - Add source_quality grader
   - Create transcript validator

## Group 4: Validation & Testing
1. **Run Contract Validation Tests**
   - Path schema validation
   - Virtual filesystem integration tests
   - Agent artifact location tests

2. **Execute Integration Tests**
   - End-to-end workflow tests
   - Multi-agent coordination tests
   - Error scenario tests

3. **Performance Baseline Tests**
   - Artifact write speed tests
   - Memory usage validation
   - Concurrent execution tests