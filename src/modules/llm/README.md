# LLM Module

The `llm` module provides integration with Large Language Models and Natural Language Processing (NLP) pipelines within the BCor system.

## Core Concepts
- **NLP Pipeline Integration**: Processes text through configurable NLP pipelines before sending to LLMs.
- **LLM Abstraction**: Uses adapter pattern (`ILlmAdapter`) to support multiple LLM providers.
- **Event-Driven Processing**: Emits events for processed text and generated responses.

## Components
- `ProcessTextCommand`: Command to process text through NLP pipeline and optionally generate LLM response.
- `GenerateResponseCommand`: Command to generate a direct response from the LLM.
- `TextProcessedEvent`: Event emitted after NLP processing.
- `ResponseGeneratedEvent`: Event emitted after LLM response generation.
- `NlpPipeline`: NLP processing engine.
- `ILlmAdapter`: Interface for LLM providers.

## Workflow
1. User sends a `ProcessTextCommand` with text and optional prompt template.
2. If `use_nlp` is enabled, text is processed through `NlpPipeline`.
3. `TextProcessedEvent` is emitted with processed text and tokens.
4. If prompt template is provided, text is formatted and sent to LLM.
5. `ResponseGeneratedEvent` is emitted with prompt and response.

## Configuration
The module requires an LLM adapter implementation. Configure the adapter in your application's `app.toml`:
```toml
[modules.llm]
adapter = "gemini"  # or "openai", "local", etc.
```

## Dependencies
- `bubus`: Event bus for message routing.
- `dishka`: Dependency injection.
- LLM-specific libraries (e.g., `google-generativeai`, `openai`).