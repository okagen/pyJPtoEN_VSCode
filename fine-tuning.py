from dotenv import load_dotenv
import os
from openai import OpenAI
import pandas as pd
import io, json

#======================================================================
# Excelファイルから日本語に対する英語表現のを取得
# Excelには「日本語」列と「英語」列があり、行ごとに対応する表現が記入されている。
def load_custom_vocab_from_excel(filename):
    df = pd.read_excel(filename)
    df = df[['日本語', '英語']].dropna()
    return dict(zip(df['日本語'], df['英語']))

#======================================================================
# 日英対照表の情報から、日本語と英語をペアにしたリストを作成
def create_vocab_instructions(vocab_dict):
    pairs = []
    for jp, en in vocab_dict.items():
        line = {jp, en}
        pairs.append(line)
    return pairs

#======================================================================
# ChatGPTモデルのファインチューニング実行
# 必要に応じて、モデルの設定を変更する必要あり
def finetuning_gpt(client, prompt_completion_pairs):
    # 学習データ生成
    lines = []
    for jp, en in prompt_completion_pairs:
        lines.append(json.dumps({
            "messages":[
                {"role":"user", "content": jp},
                {"role":"assistant", "content": en}
            ]
        }, ensure_ascii=False))
    body = "\n".join(lines) + "\n"
    buffer = io.BytesIO(body.encode("utf-8"))
    buffer.name = "vocab_chat.jsonl"

    # ファインチューニング実施
    upload = client.files.create(file=buffer, purpose="fine-tune")
    job = client.fine_tuning.jobs.create(
        training_file=upload.id,
        model="gpt-3.5-turbo-0125"
    )
    return job

#======================================================================
# ファインチューニング状況確認　30秒ごとに状態を表示する
# モデルの生成はOpenAI diveloper's platform上で状況確認できるので、
# この処理が終わる前に強制終了しても問題ない。
def wait_for_ft_job(client, job_id):
    import time
    while True:
        resp = client.fine_tuning.jobs.retrieve(job_id)
        print("Status:", resp.status)
        if resp.status in ("succeeded", "failed"):
            return resp
        time.sleep(30)

# Example usage
if __name__ == "__main__":

    load_dotenv()
    vocab_excel = "日英対照表.xlsx"
    vocab_dict = load_custom_vocab_from_excel(vocab_excel)
    vocab_pairs = create_vocab_instructions(vocab_dict)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_2"))
    job = finetuning_gpt(client, vocab_pairs)
    print(f"Fine-Tune Job ID: {job.id}; status: {job.status}")
    print("------------------")

    resp = wait_for_ft_job(client, job.id)
    ft_model = resp.fine_tuned_model
    print(f"Fine-Tune Model ID: {ft_model}")
    print("===  model is ready ====")
