from dotenv import load_dotenv
import os
from openai import OpenAI
#from openai.error import OpenAIError

# このプログラムを実行すると、MODEL_IDで指定したFine-tuningのモデルは確かに利用できなくなる。
# ただし、OpenAI developer platformのDashboardの、Fine-tuningのジョブ一覧が削除されるわけではない。
# つまり、Dashboardの、Fine-tuningのジョブ一覧は残り続ける。　2025.8.28

def main():
    load_dotenv()

    MODEL_ID = os.getenv("DEL_MODEL_ID")

    client = OpenAI(
        api_key=os.getenv("API_9519-01_TRY"),
        organization=os.getenv("OPENAI_ORG_ID"),   # ← モデルの属するOrg
#        project=os.getenv("OPENAI_PROJECT_ID"),    # ← モデルの属するProject
    )

    # 1) まずモデルの所在を確認
    try:
        info = client.models.retrieve(MODEL_ID)
        print("model found. owner/org/project (if available):", info)
    except Exception as e:
        print("retrieve failed:", e)
        return

    # 2) 削除
    try:
        resp = client.models.delete(MODEL_ID)
        print(f"Deleted: {MODEL_ID} -> {resp.deleted}")
    except Exception as e:
        # 権限エラーの中身を見たい
        print("delete failed:", e)

def chkFineTunedModels():
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("API_9519-01_TRY"),
        organization=os.getenv("OPENAI_ORG_ID"),     # 必要なら
        project=os.getenv("OPENAI_PROJECT_ID"),      # ★ここを指定すると、そのProjectに可視なモデルだけになる
    )

    # そのキーで“見える”モデルだけが返る
    models = client.models.list()

    # 例：自分で作ったFTモデルだけ見たい場合（ft: でフィルタ）
    # ここで表示されるモデルは、Projectに紐づくモデル。API Keyに紐づくものではない。
    ft_models = [m.id for m in models.data if m.id.startswith("ft:")]
    print("\n".join(ft_models))

if __name__ == "__main__":
    #main()

    # Projectを指定して、その中に存在するモデルの一覧を表示する。
    # モデルを削除する前後の確認用。
    chkFineTunedModels()
