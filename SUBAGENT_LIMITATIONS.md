# OpenCode Sub-Agent Architecture & Model Limitations

## Context
During the analysis of Liverpool's managerial transition (Alonso vs. Slot), a request was made to dispatch a sub-agent utilizing a specific foundation model (e.g., Anthropic's "Opus 4.7"). 

## Technical Reality
Unlike multi-LLM frameworks such as Claude Code, Aider, or AutoGen—which can dynamically route API requests to different providers (OpenAI, Anthropic, Gemini) if provided with the respective API keys—the OpenCode environment operates on a different architectural harness.

### Key Differences
1. **Tool Schema Constraints:** The OpenCode `Task` tool exposes three parameters: `description`, `prompt`, and `subagent_type` (e.g., "explore", "general"). It **does not** expose a parameter for `model_id` or `provider`.
2. **Unified Foundation:** All spawned sub-agents in OpenCode run on the host's globally configured model. In the current environment, both the primary agent and all sub-agents are powered by `gemini-3.1-pro-preview`.
3. **Persona Emulation vs. True Routing:** When instructed to use "Opus" or "GPT-4", the primary agent passes this request as a *persona instruction* within the sub-agent's prompt. The sub-agent effectively role-plays the requested model's behavior and scrutiny level, but physically executes on the Gemini infrastructure.

## Implications for Rigor
While true cross-model adversarial testing is impossible in this specific harness, prompting sub-agents with "maximum effort" and specific expert personas (e.g., "Elite Sports Data Scientist") successfully forces the underlying model into a highly critical state. This was demonstrated when the simulated "Opus" sub-agent successfully identified complex domain-specific flaws, such as Gerardo Seoane's contamination of Xabi Alonso's data and pitch geometry math errors.
