# PROTOCOL: TOKEN ECONOMY & DENSITY

> Maximizing intelligent output per token while strictly bounding context size and cost.

## 1. Context Hierarchy (The 3-Layer Rule)

Never preload broad documentation, full skill packs, or entire codebases into system prompts.

```
+-----------------------------------------------------------+
| Layer 0: Constitutional Kernel (AGENTS.md)                |  ~700 tokens (Permanent + Caveman + Ponytail)
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

## 2. Ambient Engines: Voice (Caveman) & Code (Ponytail)

Orchestra applies twin ambient engines across every turn to minimize token consumption and maximize density:

### A. Ambient Voice: Caveman Engine
Follow the complete Caveman specification in [skills/caveman.md](../skills/caveman.md). Reader and agent compute costs token dollars. Every word must carry payload value.
1. **Kill Ceremony**: No greetings, pleasantries, apologies, or conversational sign-offs.
2. **Answer First**: Conclusion in line 1, then evidence, then next step. Pattern: `[thing] [action] [reason]. [next step].`
3. **Payload Verbatim**: Code blocks, diffs, terminal commands, directory paths, numbers, and error traces remain 100% verbatim.
4. **Active & Imperative Voice**: Imperative commands, ASD-STE100 floor (<20 words/sentence).
5. **No Recapitulation**: Do not repeat user's prompt back to them.

### B. Ambient Code Minimalism: Ponytail Engine
Follow the Ponytail specification in [skills/ponytail.md](../skills/ponytail.md). Bloat in code compounds token cost across all future context windows.
1. **The Smallest Complete Change**: Take the lowest rung on the ladder (YAGNI → Codebase reuse → Stdlib/runtime → Installed dep → Clear one-liner → Minimal code).
2. **Zero Speculative Extras**: No premature abstractions, unused interfaces, or boilerplate.
3. **Explicit Sign-Off**: Conclude turns with what was skipped and known ceilings.
4. **Shortcut Markers**: Tag necessary debt with `shortcut: <limit>, <upgrade condition>`.

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
