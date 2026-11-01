# Contract Fix & Infrastructure Setup - Requirements

## Scope
- Fix broken agent path contracts from `/workspace/research/` to `/projects/{project_slug}/`
- Migrate all subagent prompts to use correct virtual filesystem paths
- Create proper evals/spec.md contract following eval-first methodology
- Initialize eval harness with isolated workspace functionality
- Update all agent code to use new virtual path scheme

## Functional Acceptance Criteria
- [x] All agent artifacts write to `/projects/{project_slug}/research/` instead of `/workspace/research/`
- [x] Supervisor can assemble final blueprint from correct virtual paths
- [x] Every prompt file has `evaluation_status: evaluated` field
- [x] evals/spec.md contains complete task contract with input/output schemas
- [x] evals/run_evals.py implements trial isolation and artifact capture
- [x] evals/evaluators.py contains code-based graders for artifact validation
- [x] All agents can run without path conflicts or duplicate files

## Edge Cases
- **Path conflicts**: Multiple agents writing to same virtual path without proper isolation
- **Virtual filesystem backend errors**: FilesystemBackend initialization failures
- **Prompt loading failures**: Missing or malformed YAML files
- **Workspace permission issues**: Insufficient write permissions in sandbox environments
- **Concurrent agent execution**: Race conditions during artifact writes

## Error Handling
- **Path validation**: Validate virtual paths before write operations
- **Filesystem errors**: Graceful handling of permission and disk space issues
- **Prompt parsing errors**: Fallback mechanisms for malformed YAML
- **Backend connectivity**: Retry logic for FilesystemBackend communication
- **Artifact verification**: Hash-based integrity checks for written files

## Strict Non-Requirements
- Do NOT create additional physical directories outside project structure
- Do NOT modify existing .env or configuration files
- Do NOT add new external dependencies without concrete need
- Do NOT implement UI components or web interfaces
- Do NOT create database schemas or persistent storage
- Do NOT implement advanced analytics or monitoring
- Do NOT add complex orchestration beyond agent coordination
- Do NOT create custom deployment scripts
- Do NOT modify existing prompt templates beyond path updates
- Do NOT implement advanced error recovery beyond basic scenarios
