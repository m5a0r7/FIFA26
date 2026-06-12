# OpenAI Agents SDK Reference

Read this only when the project uses the OpenAI Agents SDK.

## Adapter Notes

- If the project exposes a sync helper that calls `Runner.run_sync(...)`, call
  that helper from async simulator code with `asyncio.to_thread(...)`.
- Do not call `Runner.run_sync(...)` directly from the RELAI simulator event
  loop.

## Tools And Mocks

- `@function_tool` exports a `FunctionTool` object, not the original Python
  callable.
- Locally reachable `FunctionTool` objects can be mocked through
  `relai.MockApplication` when the adapter returns the framework agent or a
  mutable tool list as `agent_or_tools`.
- Hosted tools such as `WebSearchTool` and `FileSearchTool` execute inside the
  model provider, so mark them `kind: "hosted_tool"` and
  `final_policy: "cannot_mock"` in `.relai/mock-manifest.json`.

## Component Targets

- OpenAI Agents `FunctionTool` component targets are supported through the tool
  protocol.
- Use `FixedComponentInput(kwargs={...})` with keys matching the tool JSON
  schema.
- Do not use positional `args` for `FunctionTool` component targets.
- In `.relai/learning-env-context.json`, write `input_guidance` for
  `FunctionTool` components in terms of named JSON-schema arguments.
