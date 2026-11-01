# Agent Path Migration & Final Integration - Requirements

## Scope
- Migrate all agent code to use new virtual path schema
- Migrate all subagent prompts to use correct virtual filesystem paths
- Create final blueprint assembly workflow
- Implement comprehensive validation and testing
- Set up production-ready agent deployment
- Create comprehensive documentation and runbooks

## Functional Acceptance Criteria
- [x] All supervisor agent code uses `/projects/{project_slug}/` paths
- [x] All subagent code uses `/projects/{project_slug}/` paths
- [x] All prompt files have correct evaluation_status
- [x] Supervisor can assemble complete blueprints from virtual paths
- [x] Agent workflows integrate with evaluation harness
- [x] CI smoke gate validates all path contracts
- [x] All agents can run end-to-end successfully
- [x] Blueprint packaging works correctly
- [x] Error handling covers path validation and recovery
- [x] Documentation is comprehensive and version-controlled

## Edge Cases
- **Path schema conflicts**: Multiple agents requesting same virtual path
- **Virtual filesystem permission errors**: Sandbox access restrictions
- **Concurrent agent execution**: File locking and write conflicts
- **Path validation failures**: Incorrect schema usage
- **Blueprint assembly errors**: Missing or corrupted artifacts
- **Integration latency**: Delays between agent handoffs
- **Resource exhaustion**: Memory or disk space issues

## Error Handling
- **Path validation errors**: Detailed error messages with suggested fixes
- **Filesystem errors**: Graceful recovery and retry logic
- **Agent communication errors**: Dead letter queues and alerts
- **Blueprint assembly errors**: Fallback generation and user guidance
- **Package creation errors**: Detailed error reporting and recovery
- **Validation errors**: Clear feedback with correction steps

## Strict Non-Requirements
- Do NOT change fundamental agent behavior beyond path fixes
- Do NOT implement advanced caching strategies
- Do NOT create custom monitoring or alerting
- Do NOT modify existing agent architectures
- Do NOT add new external integrations
- Do NOT change evaluation metrics or scoring
- Do NOT implement complex orchestration beyond coordination
- Do NOT create custom deployment scripts
- Do NOT modify existing prompt templates beyond path updates
- Do NOT implement advanced error recovery beyond basic scenarios
