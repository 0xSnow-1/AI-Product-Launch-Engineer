# Project:
AI Product Launch Engineer

- An autonomous AI system that transforms a product idea into an evidence-backed product launch blueprint.

## Scope
- Who are the users? what are their problems?
- what type of outcome do we want to improve?
- Where does the agent fit in the problem/workflow?
- Level of Autonomy?

Assumptions:

- what are the data we gonna be using to test this?
- What are the inputs?
- what are the outputs?
A structured, validated launch blueprint with supporting research, decisions, and generated project artifacts.
- operational costs?
- Risk in action?


(HARNESS ARCHITECTURE)
Does the agent need to read anything to reach it's objective?
- No, no rag is needed here

Does the agent need to Act on anything?
- yes, it must implemend a Todo list writing the needed tasks
- it must delegate the tasks to subagents
- it must return all the results into the VFS
- it must read, convert the deliverable into a .zip back to the user.


Does the agent need to Have any Memories?

- yes, Working memory (default) and Procedural memory (SKILLS.md) for all 3 sub agents


What are the subagents to implement?

- Market research subagent (Research Competitors, Market Opportunities, Evidences)
- Customer Research ICP, personas, customer problems
- GTM Strategy positining, messaging, distribution

Structure:
ai-product-launch-engine/
│
├── main.py
├── src/
│   ├── prompts.py
│   ├── schemas.py
│   ├── config.py
│   │
│   ├── tools/
│   │   └── __init__.py
│   │
│   ├── subagents/
│   │   └── __init__.py
│   │
│   ├── workflows/
│   │   └── __init__.py
│   │
│   └── backends/
│       └── __init__.py
├── evals/
│   ├── datasets/
│   ├── evaluators.py
│   └── run_evals.py
├── tests/
├── langgraph.json
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md