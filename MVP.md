# MVP Specification — AI Product Launch Intelligence Engine

**Project:** AI Product Launch Intelligence & Visualization Engine  
**Version:** V1 / MVP  
**Status:** In Development

---

# 1. Product Objective

Build a Slack-based AI application that takes a product idea and produces an evidence-backed market assessment, customer analysis, go-to-market strategy, and a collection of professionally designed visual deliverables.

The application uses multiple specialist agents coordinated by a Supervisor Deep Agent.

The goal is to demonstrate a complete, functional, end-to-end agentic workflow built with LangChain Deep Agents.

**Core user experience:**

1. A user submits a product idea through Slack.
2. The Supervisor coordinates market and customer research.
3. Research agents investigate independently and produce structured findings.
4. The Supervisor evaluates their findings and presents strategic alternatives.
5. The user selects a strategic direction, or autonomous mode selects the recommended direction.
6. The GTM Strategist develops the go-to-market strategy.
7. The Design Agent transforms validated research and strategy into visual deliverables.
8. The completed Launch Decision Pack is delivered to the user through Slack.

The MVP should prioritize a reliable, complete workflow over additional features or architectural complexity.

# 2. MVP Architecture

## User Interface
- Slack application.
- Slack Bolt for Python.
- Slack commands, messages, interactive buttons, and file delivery.

## Backend
- Python.
- FastAPI where an HTTP application interface is required.
- PostgreSQL for application-level persistence.
- Environment variables for configuration and secrets.

## Agent Architecture
- LangChain Deep Agents.
- Supervisor Deep Agent.
- Ephemeral/async subagents for specialist delegation.
- TodoListMiddleware for supervisor task planning.
- Filesystem Backend for agent workspace and research artifacts.
- Pydantic for structured output validation.

## Research
- Tavily for web research.
- Amazon Bedrock / Claude Haiku 4.5 for model inference.

## Visual Production
- LangChain Design Agent running as a separate service.
- HTTP API integration.
- Generated assets stored separately from temporary agent workspace files.

## Storage Responsibilities
- PostgreSQL: projects, execution status, approvals, task status, and metadata.
- Filesystem Backend: agent working files and intermediate research artifacts.
- Final artifact storage: generated reports, images, and other user-facing deliverables.

Do not introduce Next.js or Streamlit into V1.

# 3. Core Agents and Responsibilities

## 3.1 Supervisor Agent

Responsibilities:
- Understand the user's product idea and execution mode.
- Plan and coordinate the workflow.
- Delegate research to specialist agents.
- Track delegated tasks and wait for completion.
- Collect and evaluate research findings.
- Identify strategic alternatives.
- Present decision options when required.
- Invoke the GTM Strategist only after all prerequisites are satisfied.
- Coordinate visual production.
- Assemble and deliver the final Launch Decision Pack.

The Supervisor should use TodoListMiddleware for planning and task tracking.

Important: TodoListMiddleware is not an execution-order enforcement mechanism. Critical workflow prerequisites must also be enforced by backend/application logic.

## 3.2 Market Researcher

Responsibilities:
- Identify direct and indirect competitors.
- Analyze competitor positioning, pricing, strengths, and weaknesses.
- Identify market opportunities and gaps.
- Investigate industry trends.
- Identify supporting evidence for material findings.
- Estimate market size only when credible evidence is available.

Output: `market_research.json`

## 3.3 Customer Researcher

Responsibilities:
- Identify relevant customer segments.
- Analyze customer pain points.
- Identify buying behavior and purchasing motivations.
- Determine potential ideal customer profiles.
- Evaluate customer needs and priorities.
- Support findings with credible sources.

Output: `customer_research.json`

## 3.4 GTM Strategist

The GTM Strategist must receive:
- Original product information.
- Market research results.
- Customer research results.
- User-approved strategic direction or autonomous recommendation.

Responsibilities:
- Develop product positioning.
- Define differentiation.
- Recommend target customer segments.
- Develop pricing hypotheses.
- Recommend customer acquisition channels.
- Develop an initial launch roadmap.
- Identify strategic risks and assumptions.

Output: `gtm_strategy.json`

The GTM Strategist must not execute until market research and customer research have completed successfully, their outputs have been validated, and the required strategic direction has been approved or selected automatically.

## 3.5 Design Agent

The Design Agent is a separate visual-production service.

It receives structured, validated information from the Supervisor/application and generates the requested assets.

Responsibilities:
- Produce visually polished deliverables.
- Follow the provided visual briefs.
- Use the supplied research and strategy data.
- Preserve factual accuracy.
- Return generated files and an asset manifest.
- Report failed or incomplete asset generation.

The Design Agent must not invent market statistics, competitor information, or research findings.

# 4. Required Workflow

Implement the following execution sequence.

### Stage 1 — Project Creation
- Receive the product idea through Slack.
- Create a unique project ID.
- Record the user's execution mode.
- Initialize project state and workspace.
- Start the Supervisor workflow.

### Stage 2 — Parallel Research
- Supervisor launches Market Researcher asynchronously.
- Supervisor launches Customer Researcher asynchronously.
- Both researchers operate independently.
- Each specialist saves its structured result in the shared project workspace.
- Supervisor tracks both tasks until completion.
- Retrieve and validate both outputs.

Do not start GTM while either research task is pending, failed, or invalid.

### Stage 3 — Strategic Decision

Supervisor evaluates the research and determines whether there are materially different strategic directions.

Support two execution modes:

**Full Autonomous Mode**
- Supervisor selects the recommended direction.
- Workflow proceeds without manual approval.

**Ambient Mode**
- Supervisor presents two strategic alternatives through Slack.
- User selects an option using interactive buttons.
- Implement an eight-second countdown.
- If no selection arrives before timeout, use the predefined default option.
- Persist the selection and approval status.

The countdown and Slack interaction must be handled by application/backend logic, not simulated through the agent's prompt.

### Stage 4 — GTM Strategy

Before invoking GTM, the application must verify:

- Market research is complete.
- Customer research is complete.
- Both research outputs passed validation.
- A strategic direction has been selected.
- Approval requirements have been satisfied.

Expose GTM execution through a guarded application tool or service.

If prerequisites are missing, reject execution.

Once eligible, invoke the GTM Strategist with the complete structured research and selected strategic direction.

Validate and persist `gtm_strategy.json`.

### Stage 5 — Visual Production

Create a canonical `launch_pack.json` containing the validated research and GTM strategy.

Prepare individual visual briefs for the Design Agent.

V1 must support these four deliverables:

1. **Competitor Positioning Map**
   - Competitor positioning.
   - Comparison dimensions.
   - Differentiation opportunities.
   - Supporting references.

2. **Customer Segmentation Infographic**
   - Customer segments.
   - Characteristics.
   - Pain points.
   - Segment priorities.

3. **GTM Roadmap**
   - Launch phases.
   - Recommended activities.
   - Acquisition channels.
   - Milestones and proposed timelines.

4. **Executive Opportunity Report**
   - Product opportunity assessment.
   - Market findings.
   - Customer findings.
   - Recommended positioning.
   - GTM strategy.
   - Risks and assumptions.
   - Supporting evidence and references.

The Design Agent must receive structured data and explicit design instructions rather than an unstructured collection of research documents.

Retrieve the generated assets through its API.

Store completed files and generate `asset_manifest.json` with asset names, types, paths, and completion statuses.

### Stage 6 — Final Delivery

Deliver the completed Launch Decision Pack through the original Slack conversation/thread.

The user should receive:
- Executive opportunity report.
- Competitor positioning map.
- Customer segmentation infographic.
- GTM roadmap.

Show completion or failure status for every deliverable.

# 5. Project Workspace Structure

Avoid unnecessary Markdown files and excessive intermediate artifacts.

Use a compact structured project workspace:

```text
projects/
└── {project_id}/
    ├── research/
    │   ├── market_research.json
    │   └── customer_research.json
    │
    ├── strategy/
    │   └── gtm_strategy.json
    │
    └── deliverables/
        ├── launch_pack.json
        ├── asset_manifest.json
        └── assets/
            ├── competitor_map.png
            ├── segmentation.png
            ├── gtm_roadmap.png
            └── executive_report.pdf
```

Adapt this structure to the existing Filesystem Backend configuration. Virtual paths must match the configured backend root.

Do not assume different agents automatically share the same filesystem. Configure the required shared backend explicitly.

Use Pydantic models to validate the schemas for research outputs, GTM strategy, launch pack, and asset manifest.

Every material research claim should have a source reference. Clearly distinguish verified facts, interpretations, assumptions, and recommendations.

# 6. MVP Implementation Todo List

Work through these phases in order.

## Phase 1 — Inspect and Stabilize the Existing Agent System

- [ ] Inspect the current repository and identify implemented features.
- [ ] Identify the existing Supervisor configuration and prompt.
- [ ] Identify registered specialist agents.
- [ ] Verify the async subagent registration and execution mechanism.
- [ ] Verify TodoListMiddleware configuration.
- [ ] Verify shared Filesystem Backend configuration.
- [ ] Verify that specialists can write and retrieve project artifacts.
- [ ] Review existing YAML prompts and remove obsolete responsibilities.
- [ ] Establish consistent Pydantic output contracts.

**Exit condition:** The existing agent system is understood, functional, and has clearly defined responsibilities.

## Phase 2 — Implement and Validate the Research Workflow

- [ ] Implement Market Researcher.
- [ ] Implement Customer Researcher.
- [ ] Run both researchers asynchronously.
- [ ] Track task IDs and completion statuses.
- [ ] Handle task failures and incomplete results.
- [ ] Persist both research outputs.
- [ ] Validate outputs before proceeding.
- [ ] Ensure the Supervisor can retrieve and synthesize both results.

**Exit condition:** Both researchers can execute independently, complete successfully, and provide validated results to the Supervisor.

## Phase 3 — Implement Human Decision and GTM Execution

- [ ] Implement Full Autonomous Mode.
- [ ] Implement Ambient Mode.
- [ ] Create structured strategic alternatives.
- [ ] Implement Slack decision buttons.
- [ ] Persist user selections.
- [ ] Implement the eight-second default-selection timeout.
- [ ] Implement backend approval validation.
- [ ] Create a guarded GTM execution tool.
- [ ] Ensure premature GTM execution is rejected.
- [ ] Implement and validate the GTM Strategist.

**Exit condition:** GTM can only execute after the research prerequisites and decision requirements are satisfied.

## Phase 4 — Slack Integration

- [ ] Create/configure the Slack application.
- [ ] Implement a project creation command.
- [ ] Receive product ideas and execution-mode selections.
- [ ] Connect Slack interactions to the Python backend.
- [ ] Post workflow progress updates.
- [ ] Present strategic alternatives using interactive buttons.
- [ ] Receive and process button selections.
- [ ] Deliver generated reports and assets.
- [ ] Handle Slack interaction retries and duplicate events safely.

**Exit condition:** A user can operate the entire workflow through Slack without using the command line.

## Phase 5 — Design Agent Integration

- [ ] Run LangChain's Design Agent locally or in a dedicated environment.
- [ ] Understand its HTTP API and file retrieval mechanism.
- [ ] Implement a Python client for sending visual briefs.
- [ ] Define reusable briefs for the four required assets.
- [ ] Send validated launch-pack data to the Design Agent.
- [ ] Retrieve completed files.
- [ ] Handle long-running tasks and generation failures.
- [ ] Create and validate the asset manifest.
- [ ] Store final assets independently from temporary agent files.

**Exit condition:** One completed research and strategy workflow can generate all four intended deliverables.

## Phase 6 — Persistence and Reliability

- [ ] Persist project records in PostgreSQL.
- [ ] Persist workflow execution states.
- [ ] Persist approval decisions.
- [ ] Persist async task statuses and results.
- [ ] Ensure Slack interactions can resume the correct project.
- [ ] Ensure state survives application restarts.
- [ ] Handle agent failures and retry recoverable operations.
- [ ] Avoid duplicate workflow execution caused by repeated Slack events.
- [ ] Keep credentials and API keys in environment variables.
- [ ] Add useful logs for debugging.

**Exit condition:** Projects and their execution states survive restarts, and recoverable failures do not require rebuilding the entire project.

## Phase 7 — Deployment and Public Release

- [ ] Deploy the Python backend.
- [ ] Deploy the Slack application.
- [ ] Deploy or connect the Design Agent service.
- [ ] Configure PostgreSQL and artifact storage.
- [ ] Configure production environment variables.
- [ ] Test both execution modes.
- [ ] Run multiple complete end-to-end test projects.
- [ ] Fix critical workflow and delivery issues.
- [ ] Write a comprehensive README.
- [ ] Add architecture and workflow diagrams.
- [ ] Add setup and deployment instructions.
- [ ] Record a product demonstration.
- [ ] Publish the repository.
- [ ] Write the first technical build-in-public article.

**Exit condition:** Another developer can understand the system, configure it, run it, and see a complete working demonstration.

# 7. What Is Explicitly Out of Scope for V1?

Do not implement these unless a core MVP requirement cannot work without them.

- Next.js frontend.
- Streamlit frontend.
- Technical Architect agent.
- Coding agent.
- Additional specialist agents.
- Multiple Design Agents.
- Video generation and animation.
- Automatic execution of marketing campaigns.
- Billing and subscription management.
- Complex multi-user permission systems.
- Multi-cloud deployment.
- Advanced analytics dashboards.
- Custom StateGraph solely for duplicating existing Deep Agent delegation.
- Excessive Markdown deliverables.
- Features that do not contribute to the end-to-end launch workflow.

# 8. Definition of MVP Success

The MVP is successful when all of the following are true:

## Functional Success

- [ ] A user can start a project through Slack.
- [ ] The two research specialists execute independently and in parallel.
- [ ] Both research results are retrieved, persisted, and validated.
- [ ] The Supervisor synthesizes research into strategic alternatives.
- [ ] Full Autonomous Mode can proceed without manual approval.
- [ ] Ambient Mode correctly handles user selection and timeout.
- [ ] GTM cannot execute prematurely.
- [ ] GTM produces a structured, validated strategy.
- [ ] The Design Agent produces the four required deliverables.
- [ ] All final deliverables reach the user through Slack.

## Engineering Success

- [ ] Agent responsibilities are clearly separated.
- [ ] The workflow does not depend exclusively on prompt instructions for critical execution rules.
- [ ] Shared filesystem behavior works as intended.
- [ ] Project state and approvals are persisted.
- [ ] Failures are visible and recoverable.
- [ ] Research claims are traceable to evidence.
- [ ] Generated visualizations do not introduce fabricated data.
- [ ] Credentials are not exposed.
- [ ] The system has been tested with at least three different product ideas.

## Public Release Success

- [ ] The application has a working deployed demonstration.
- [ ] The repository has a useful README.
- [ ] Architecture and implementation decisions are documented.
- [ ] Another developer can reproduce the setup.
- [ ] A demonstration video is available.
- [ ] The first technical article is published.

**The MVP is not required to achieve perfect research or strategy recommendations. It must demonstrate a reliable,