# Question for Later

## Current evals/spec.md Content

```
(QUESTION FOR LATER DONT SEE)

okay so here is the thing, i dont understand the input part, shouldnt we enforce a pydantic schema in which it uses a basemodel class of things (read @ai-product-launch-engine/evals/spec.md ) in langchain i couldve created a node that extracts them used pydantic basemodel and returns them as a string to power the subagents, what is the solution for this?  does deepagents have a paremter for example in which we can use? and also shall we implement a "assumptions" field as well where the LLM will convert the user's query into a final assumption and put the entire result into a breif.md (check) and before it executes to the sub agent it sends an interrupt? where it sends it back to the human fo rreview and if the choose edit, the agent checks the user's answer, learn's from it and modifies the brief, then send'sa  preview once again, if the user says accept, then the main agent proceeds to delegate to the subagents, subagents will have an idea to read the breif .md (market research, and customer researcher NOT the GTM agent) i want to solve this part of the problem so please research deepagents document, or langchain, find solutions and come back with a proposal wirtten ina  markdown for me to review and decide on what our next move shall be 
```

## Summary

This is the existing content of `/home/snowaflic/GTM-autonomous/ai-product-launch-engine/evals/spec.md` that was a question/dump rather than a proper contract. This content should be preserved for reference and future resolution, as it contains important questions about:

- Pydantic schema implementation for input validation
- DeepAgents parameter configuration
- Assumption handling in the agent workflow
- Human-in-the-loop review processes
- Agent coordination and briefing structure

This content needs to be addressed in Phase 1 or Phase 2 of the project implementation.