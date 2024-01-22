from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


def get_comment(post: str, role: str, temperature: float):
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": f'{post}'}
        ],
        max_tokens=200,
        temperature=temperature,
    )

    return completion.choices[0].message.content


def get_dialog_phrase(context: list[str], role: str, temperature: float):
    messages = [{'role': 'system', 'content': role}, {'role': 'user', 'content': context[-1]}]
    for i, phrase in enumerate(context[1:]):
        messages.append({'role': 'assistant' if i % 2 == 0 else 'user',
                         'content': phrase})
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=200,
        temperature=temperature
    )

    return completion.choices[0].message.content
