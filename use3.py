from openai import OpenAI
import os
from datetime import datetime
from dotenv import load_dotenv

# APIキーを環境変数から取得（Service Account のキー）
load_dotenv()
api_key = os.getenv("API_9519-01_TRY")  # Service Account の APIキー

client = OpenAI(api_key=api_key)

# ツール（関数）の定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "現在の時刻を返します",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }
    }
]

# 実際のツール実装（ローカル処理）
def get_current_time():
    now = datetime.now().isoformat()
    return {"current_time": now}

# チャットの実行（Tool callのトリガー）
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "今何時？"}
    ],
    tools=tools,
    tool_choice="auto"  # ツールが必要なときだけ呼び出す
)

# ツール呼び出しの検出と実行
tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        if function_name == "get_current_time":
            result = get_current_time()

            # ツールレスポンスをメッセージとして送る
            second_response = client.chat.completions.create(
                model="gpt-4-0613",
                messages=[
                    {"role": "user", "content": "今何時？"},
                    response.choices[0].message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result),
                    }
                ]
            )

            print("Assistant response:", second_response.choices[0].message.content)
else:
    print("Tool call was not triggered.")
