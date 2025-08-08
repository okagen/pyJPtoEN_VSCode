import os
from openai import OpenAI
from dotenv import load_dotenv

# .env からAPIキー読み込み
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY_006-2")  # Service Account の APIキー
#api_key = os.getenv("OPENAI_API_KEY_SA_006")  # Service Account の APIキー

# 新しいClientオブジェクトを使う
client = OpenAI(api_key=api_key)

# Chat Completion 呼び出し
response = client.chat.completions.create(
    model="gpt-4",  # または gpt-3.5-turbo
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "サービスアカウントのメリットを説明してください。"}
    ],
    temperature=0.7,
)

# 結果の出力
print(response.choices[0].message.content)
