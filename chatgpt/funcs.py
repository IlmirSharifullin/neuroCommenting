import asyncio
import base64
import os

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


async def get_comment(post: str, role: str, photo_path: str = None):
    # start_time = datetime.datetime.now()
    photo_path = None
    if photo_path is not None:
        base64_image = encode_image(photo_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": post
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                'detail': 'low'
                            },
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        completion = response.json()
        answer = completion['choices'][0]['message']['content']
        return answer
    else:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": f'{post}'}
            ],
            max_tokens=200,
        )

        return completion.choices[0].message.content


def get_dialog_phrase(context: list[str], role: str):
    messages = [{'role': 'system', 'content': role}, {'role': 'user', 'content': context[-1]}]
    for i, phrase in enumerate(context[1:]):
        messages.append({'role': 'assistant' if i % 2 == 0 else 'user',
                         'content': phrase})
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        max_tokens=200,
    )

    return completion.choices[0].message.content
