from os import environ
from google import google_genai
from google.genai import google_types
from typing import Union
import logging

async def completion(prompt: Union[str, list, google_types.Content],
                     model_name: str,
                     system_instruction: str = None,
                     client_session: google_genai.Client = None,
                     return_text: bool = True,
                     **additional_params):
    
    # Use provided client session or default
    if client_session:
        logging.info("Using provided Google GenAI client session.")
        _client = client_session
    else:
        logging.info("Using default Google GenAI client session.")
        _client = google_genai.Client(api_key=environ.get("GEMINI_API_KEY"))

    # Construct parameters
    _gparams = {}

    # Check if we have system instruction
    if system_instruction:
        _gparams["system_instruction"] = system_instruction

    # Append additional parameters
    if additional_params:
        _gparams.update(additional_params)

    # Create response
    _response = await _client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=google_types.GenerateContentConfig(**_gparams)
    )

    if return_text:
        return _response.text
    else:
        return _response