from core.config import config
from typing import Union
import logging
import openai

async def completion(prompt: Union[str, list],
                     model_name: str,
                     system_instruction: str = None,
                     client_session: openai.AsyncClient = None,
                     return_text: bool = True,
                     **additional_params):

    # Use provided client session or default
    if client_session:
        logging.info("Using provided OpenAI client session.")
        _client = client_session
    else:
        logging.info("Using default OpenAI client session.")
        _client = openai.AsyncClient(api_key=config.get("api_keys.openai_api_key"))

    # Construct parameters
    _oparams = {}

    # Append additional parameters
    if additional_params:
        _oparams.update(additional_params)

    # Construct prompt
    _prompts = []
    if type(prompt) == str:
        _formatted_prompt = [{"role": "user", "content": prompt}]
    else:
        _formatted_prompt = prompt

    # Append the prompt if we have system instruction
    if system_instruction:
        _prompts.append({"role": "system", "content": system_instruction})
    _prompts.extend(_formatted_prompt)
    
    # Create response
    _response = await _client.chat.completions.create(
        model=model_name,
        messages=_prompts,
        **_oparams
    )

    if return_text:
        return _response.choices[0].message.content
    else:
        return _response