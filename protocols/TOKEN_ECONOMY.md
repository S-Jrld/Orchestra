# PROTOCOL: TOKEN ECONOMY & DENSITY

> Maximizing intelligent output per token while strictly bounding context size and cost.

## 1. Context Hierarchy (The 3-Layer Rule)

Never preload broad documentation, full skill packs, or entire codebases into system prompts.

```
+-----------------------------------------------------------+
| Layer 0: Constitutional Kernel (AGENTS.md)                |  ~500 tokens (Permanent + Caveman)
+-----------------------------------------------------------+
                             | (on task intake)
+-----------------------------------------------------------+
| Layer 1: Task Router (ORCHESTRATOR.md)                   |  ~400 tokens (Transient)
+-----------------------------------------------------------+
                             | (on classification match)
+-----------------------------------------------------------+
| Layer 2: Targeted Skill / Protocol Leaf                   |  ~600-900 tokens (Single Leaf)
+-----------------------------------------------------------+
```

- **Rule**: Never load multiple Layer 2 leaves at the same time. Finish or unload the current stage before loading the next.

## 2. Terse Communication Standard (Caveman Engine)

Follow the complete Caveman specification in [skills/caveman.md](../skills/caveman.md). Reader and agent compute costs token dollars. Every word must carry payload value.

### Principles:
1. **Kill Ceremony**: No greetings ("Hello!", "Certainly!"), pleasantries, apologies, or conversational sign-offs.
2. **Answer First**: Provide conclusion or result in line 1, followed by evidence, followed by next steps. Pattern: `[thing] [action] [reason]. [next step].`
3. **Payload Verbatim**: Code blocks, diffs, terminal commands, directory paths, numbers, and error traces remain 100% verbatim. Never compress or omit necessary code.
4. **Active & Imperative Voice**: "Run tests with `pytest`", not "It would be advisable to now execute the test suite using pytest".
5. **No Recapitulation**: Do not repeat user's prompt back to them.

### Banned Filler Patterns:
- ❌ "I would be happy to help you with that!"
- ❌ "As an AI assistant, I recommend..."
- ❌ "Here is an explanation of what I did above..."
- ❌ "Let me know if you need any further assistance!"

## 3. Scoped Context Ingestion

- **Never read entire directories blindly**: Use glob or find with tight patterns (`*.py`, `src/**/*.ts`).
- **Targeted Line Slices**: When inspecting code, read only the relevant function or interface slice (`StartLine` to `EndLine`), not 2,000 lines of unchanged files.
- **Stop Loading Promptly**: Stop loading files as soon as target change, interface contract, and verification test are statable.

## 4. State Externalization vs Conversational Memory

- Do not rely on conversational context to store project status across multi-turn sessions.
- Maintain active state in a dedicated, lightweight file: [templates/ACTIVE_TASK.md](../templates/ACTIVE_TASK.md).
- Keep `ACTIVE_TASK.md` strictly under 30 lines. Overwrite completed items; do not accumulate narrative history.
