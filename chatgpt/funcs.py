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


async def get_comment(post: str, role: str, photo_path: str):
    # start_time = datetime.datetime.now()
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
        print(completion)
        answer = completion['choices'][0]['message']['content']
        return answer
    else:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": f'{post}'}
            ],
            max_tokens=200,
        )

        return completion.choices[0].message.content

    # end_time = datetime.datetime.now()
    # sleep_time = math.ceil(WORKING_TIME - (end_time - start_time).total_seconds())
    # print(sleep_time)
    # time.sleep(max(0, sleep_time))

    # casual = await get_casual(completion.choices[0].message.content)


#
# async def get_casual(text: str):
#     assistant = client.beta.assistants.create(
#         name="Casual",
#         instructions=f"Я хочу, чтобы ты переделывал мои сообщения (комментарии к постам) в разговорный стиль. Я буду давать комментарий, а ты его будешь переделывать под более разговорный. Не пиши слишком много, суть должна прослеживаться та же. Не удлинняй данный текст. Можешь даже сделать его короче. You are - {sex} and {age} years old. It is commentaries to some posts, not a 1v1 dialog. Не будь фамильярным.",
#         model="gpt-3.5-turbo"
#     )
#     assistant_id = assistant.id
#     print(assistant_id)
#     thread = client.beta.threads.create()
#
#     message = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role='user',
#         content=text
#     )
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=assistant_id,
#     )
#     run = client.beta.threads.runs.retrieve(
#         thread_id=thread.id,
#         run_id=run.id
#     )
#     while run.status != 'completed':
#         print(run.status)
#         await asyncio.sleep(10)
#         run = client.beta.threads.runs.retrieve(
#             thread_id=thread.id,
#             run_id=run.id
#         )
#
#     messages = client.beta.threads.messages.list(
#         thread_id=thread.id
#     )
#     return messages.data[0].content[0].text.value


# asyncio.run(get_comment('Случился пожар на улице Пушкина', '''Ты Игорь, ученик школы. из города Елабуга. Знаток города. Патриот России, но не всегда довольна местной властью. Мало что знаешь про политику.
# Всегда следуешь тону и стилю роли Игорь.
# not a 1v1 dialog.
# Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота.
# Задача писать живые комментарии.  Оспаривайте любые факты и доводы, просто потому, что.
# ''', 'img.png'))
