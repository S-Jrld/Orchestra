# Orchestra Development Roadmap

Future enhancements for the Orchestra AI orchestration framework.

## Planned Capabilities

1. **Client Adapters**:
   - Claude Code adapter (`.claude-plugin/plugin.json`).
   - Cursor Rules adapter (`.cursorrules`).
   - GitHub Copilot CLI adapter.
   - MCP (Model Context Protocol) Server exposing Orchestra workflows as dynamic tools.

2. **Distributed & Remote Workers**:
   - Support for remote subagent dispatch across SSH or containerized Docker sandboxes.
   - Streaming NDJSON execution events.

3. **Semantic Retrieval Augmentation (Optional)**:
   - Optional local vector index (using sqlite-vss or pure numpy embeddings) for hybrid deterministic + semantic skill routing when prompt vocabulary is highly ambiguous.

4. **Interactive Step Approval TUI**:
   - Terminal user interface for reviewing pending step contracts and inspecting diffs before authorizing execution.
