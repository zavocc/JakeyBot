Insert this code of block on file [`/cogs/ai/tasks/message_actions.py - MessageActions:explain()`](./cogs/ai/tasks/message_actions.py) on line 103
```py
if message.attachments:
    for _index, _attachment in enumerate(message.attachments):
        if _index > 4:
            break

        if _attachment.size > 5500000:
            continue

        if any(_iter in _attachment.content_type for _iter in ["image"]):
            if _default_model_config["sdk"] == "openai":
                _constructed_prompt.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": _attachment.url
                        }
                    ]
                })

            else:
                _constructed_prompt.append({
                    "role": "user",
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": _attachment.content_type.split(";")[0],
                                "data": (await base64.b64encode(await _attachment.read())).decode("utf-8")
                            }
                        }
                    ]
                })

        _embed.add_field(name="File added to context:", value=_attachment.url, inline=False)
```