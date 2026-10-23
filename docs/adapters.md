# Orchestra Client Adapters Architecture

Orchestra uses a standardized adapter interface (`ClientAdapter`) to decouple orchestration logic from specific AI agent hosts and tools.

## The Canonical Adapter Interface

Every client adapter must implement:

```python
class ClientAdapter(ABC):
    @abstractmethod
    def get_name(self) -> str: ...
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]: ...
    @abstractmethod
    def validate_environment(self) -> Tuple[bool, List[str]]: ...
    @abstractmethod
    def install_skills(self, skills: List[SkillManifest], target_dir: str) -> List[str]: ...
    @abstractmethod
    def invoke_step(self, step: WorkflowStep, contract: TaskContract, context: Dict[str, str]) -> StructuredResult: ...
    @abstractmethod
    def cancel(self, run_id: str) -> None: ...
```

## Available Adapters

- **Mock Adapter (`mock`)**: Fast, in-memory harness for automated testing and CI.
- **OpenCode Adapter (`opencode`)**: Global and project-level integration for OpenCode.
- **Antigravity CLI Adapter (`antigravity`)**: Workspace integration for Google Antigravity CLI.
- **Cursor Adapter (`cursor`)**: Workspace integration for Cursor IDE (`.cursor/rules/orchestra.mdc`).
- **Claude Code Adapter (`claude`)**: CLI integration for Anthropic Claude Code (`CLAUDE.md`).

## Diagnostic Commands

```bash
# List registered adapters
orch adapters list

# Run adapter health checks
orch adapters doctor
```
