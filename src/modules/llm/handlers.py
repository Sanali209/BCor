"""Command handlers for the LLM module."""
from __future__ import annotations

import logging

from bubus import EventBus

from src.modules.llm.domain.interfaces.llm import ILlmAdapter
from src.modules.llm.domain.nlp_pipeline import NlpPipeline
from src.modules.llm.messages import (
    GenerateResponseCommand,
    ProcessTextCommand,
    ResponseGeneratedEvent,
    TextProcessedEvent,
)

logger = logging.getLogger(__name__)


async def handle_generate_response(
    cmd: GenerateResponseCommand,
    llm: ILlmAdapter,
    event_bus: EventBus,
) -> None:
    """Handle a command to generate an LLM response."""
    logger.info(f"Generating LLM response for: {cmd.prompt[:50]}...")
    
    response = await llm.generate_response(cmd.prompt)
    
    await event_bus.dispatch(
        ResponseGeneratedEvent(prompt=cmd.prompt, response=response)
    )


async def handle_process_text(
    cmd: ProcessTextCommand,
    nlp: NlpPipeline,
    llm: ILlmAdapter,
    event_bus: EventBus,
) -> None:
    """Handle a command to process text through NLP and then LLM."""
    logger.info(f"Processing text: {cmd.text[:50]}...")
    
    processed_text = cmd.text
    tokens = []
    
    if cmd.use_nlp:
        nlp.set_text(cmd.text)
        # In a real system, we'd load rules from a repository here
        # For now, let's assume a basic run
        nlp.run()
        processed_text = nlp.get_text()
        tokens = nlp.get_tokens()
    
    await event_bus.dispatch(
        TextProcessedEvent(
            original_text=cmd.text,
            processed_text=processed_text,
            tokens=tokens,
        )
    )
    
    # After NLP, generate LLM response if a template is provided
    prompt = processed_text
    if cmd.prompt_template:
        prompt = cmd.prompt_template.format(text=processed_text)
    
    response = await llm.generate_response(prompt)
    
    await event_bus.dispatch(
        ResponseGeneratedEvent(prompt=prompt, response=response)
    )
