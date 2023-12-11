import os
import time

import asyncio
import openai
from openai import OpenAI
from dotenv import load_dotenv

from db.models import SexEnum

load_dotenv()

client = OpenAI()

assistant_role = "You are an ordinary social media user, casually commenting on public updates. Your comments should sound like genuine human responses, including a few mistakes to make them more natural. Try to incorporate emotions, reflections from personal experiences, and everyday conversational phrases into your comments. Embrace your individual style and feel free to use informal language. Additionally, ensure that the length of your comments falls within the range of 50 to 250 characters. Use casual language and throw in an occasional emoticon. Do not write too much please."


async def get_comment(post: str, sex):
    global assistant_role
    sex = SexEnum(sex)
    age = 40
    assistant_role += f"You are {sex.name} from Russia and you talk in Russian. And also are patriot of Russia, you are {age} years old. And you also do not understand english"
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": assistant_role},
            {"role": "user", "content": f"""Пост: {post}"""}
        ],
        max_tokens=200,
    )
    print(completion.choices[0].message.content)
    casual = await get_casual(completion.choices[0].message.content, sex, age)

    return casual


async def get_casual(text: str, sex, age):
    assistant = client.beta.assistants.create(
        name="Casual",
        instructions=f"Я хочу, чтобы ты переделывал мои сообщения (комментарии к постам) в неформальный разговорный стиль. Я буду давать комментарий, а ты его будешь переделывать под более разговорный и неформальный. Не пиши слишком много, суть должна прослеживаться та же. Не удлинняй данный текст. Можешь даже сделать его короче. You are - {sex} and {age} years old.",
        model="gpt-3.5-turbo"
    )
    assistant_id = assistant.id
    print(assistant_id)
    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=text
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    while run.status != 'completed':
        print(run.status)
        await asyncio.sleep(10)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    return messages.data[0].content[0].text.value
