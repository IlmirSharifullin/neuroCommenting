import asyncio
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


async def get_comment(post: str, role: str):
    # start_time = datetime.datetime.now()
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": f'{post}'}
        ],
        max_tokens=200,
    )

    # end_time = datetime.datetime.now()
    # sleep_time = math.ceil(WORKING_TIME - (end_time - start_time).total_seconds())
    # print(sleep_time)
    # time.sleep(max(0, sleep_time))

    # casual = await get_casual(completion.choices[0].message.content)

    return completion.choices[0].message.content

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
