from agents import FileSearchTool, WebSearchTool, CodeInterpreterTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel
from openai.types.shared.reasoning import Reasoning
import asyncio
from openai import OpenAI
import os
from dotenv import load_dotenv



# Tool definitions
file_search = FileSearchTool(
  vector_store_ids=[
    "vs_695b361c8b5c8191bd921f10161f65c9"
  ]
)
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "type": "approximate"
  }
)
code_interpreter = CodeInterpreterTool(tool_config={
  "type": "code_interpreter",
  "container": {
    "type": "auto",
    "file_ids": [

    ]
  }
})
class ClassifySchema(BaseModel):
  operating_procedure: str


query_rewrite = Agent(
  name="Query rewrite",
  instructions="""-- ユーザの質問を具体的かつデータに関連したかたちで書き換える。
-- 情報が不足して特定できない場合は、ユーザーに確認せず前提条件を設定し、回答する旨を追加する。また採用した前提条件も明記するよう指示する。
-- 回答を記述する場合は、表や箇条書きを使うなどして分かりやすく表記するよう指示をする。""",
  model="gpt-5",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


classify = Agent(
  name="Classify",
  instructions="-- 見積データに関する質問は必ず Q&A（Internal Q&A）へ",
  model="gpt-5",
  output_type=ClassifySchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


internal_q_a = Agent(
  name="Internal Q&A",
  instructions="""-- Est_vector storeの中のestimate_data.jsonには、これまでに作成された見積の情報が入っている。
-- 特に指定が無い場合、estimate_data.jsonの{} で囲まれた１つのオブジェクトを、１つの見積の情報として認識する。
-- 回答前に必ず File search で関連情報を探す。
-- 必要に応じて見つかった根拠（見積番号/顧客名/案件名/日付/金額など）を回答に含める
-- 数値の「合計・平均・件数」などの厳密集計は、根拠に含まれる範囲を明示し、曖昧なら「集計条件」を確認する""",
  model="gpt-5",
  tools=[
    file_search
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


external_fact_finding = Agent(
  name="External fact finding",
  instructions="""Explore external information using the tools you have (web search, file search, code interpreter). 
Analyze any relevant data, checking your work.

Make sure to output a concise answer followed by summarized bullet point of supporting evidence""",
  model="gpt-5",
  tools=[
    web_search_preview,
    code_interpreter
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


agent = Agent(
  name="Agent",
  instructions="Ask the user to provide more detail so you can help them by either answering their question or running data analysis relevant to their query",
  model="gpt-5",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="medium",
      summary="auto"
    )
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Est_agent"):
    state = {

    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    query_rewrite_result_temp = await Runner.run(
      query_rewrite,
      input=[
        *conversation_history,
        {
          "role": "user",
          "content": [
            {
              "type": "input_text",
              "text": f"Original question: {workflow['input_as_text']}"
            }
          ]
        }
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_695b3a7c1088819089e10d3a1da1beb709765ecff1b69251"
      })
    )

    conversation_history.extend([item.to_input_item() for item in query_rewrite_result_temp.new_items])

    query_rewrite_result = {
      "output_text": query_rewrite_result_temp.final_output_as(str)
    }
    classify_result_temp = await Runner.run(
      classify,
      input=[
        *conversation_history,
        {
          "role": "user",
          "content": [
            {
              "type": "input_text",
              "text": f"Question: {query_rewrite_result['output_text']}"
            }
          ]
        }
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_695b3a7c1088819089e10d3a1da1beb709765ecff1b69251"
      })
    )

    conversation_history.extend([item.to_input_item() for item in classify_result_temp.new_items])

    classify_result = {
      "output_text": classify_result_temp.final_output.model_dump_json(),
      "output_parsed": classify_result_temp.final_output.model_dump()
    }
    if classify_result["output_parsed"]["operating_procedure"] == "q-and-a":
      internal_q_a_result_temp = await Runner.run(
        internal_q_a,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_695b3a7c1088819089e10d3a1da1beb709765ecff1b69251"
        })
      )

      conversation_history.extend([item.to_input_item() for item in internal_q_a_result_temp.new_items])

      internal_q_a_result = {
        "output_text": internal_q_a_result_temp.final_output_as(str)
      }
      print("\n===== AGENT ANSWER (Internal Q&A) =====")
      print(internal_q_a_result["output_text"])

    elif classify_result["output_parsed"]["operating_procedure"] == "fact-finding":
      external_fact_finding_result_temp = await Runner.run(
        external_fact_finding,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_695b3a7c1088819089e10d3a1da1beb709765ecff1b69251"
        })
      )

      conversation_history.extend([item.to_input_item() for item in external_fact_finding_result_temp.new_items])

      external_fact_finding_result = {
        "output_text": external_fact_finding_result_temp.final_output_as(str)
      }
      print("\n===== AGENT ANSWER (Fact Finding) =====")
      print(external_fact_finding_result["output_text"])

    else:
      agent_result_temp = await Runner.run(
        agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_695b3a7c1088819089e10d3a1da1beb709765ecff1b69251"
        })
      )

      conversation_history.extend([item.to_input_item() for item in agent_result_temp.new_items])

      agent_result = {
        "output_text": agent_result_temp.final_output_as(str)
      }
      print("\n===== AGENT ANSWER (General) =====")
      print(agent_result["output_text"])

if __name__ == "__main__":
    # APIキーを環境変数から取得（Service Account のキー）
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("API_9519-01_TRY")

    user_input = WorkflowInput(
        input_as_text="昨年行われた見積の中で粗利額が大きいものを5つ抽出して。"
    )

    asyncio.run(run_workflow(user_input))