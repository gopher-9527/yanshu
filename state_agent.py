"""
异步图片生成 Agent

实现架构：
1. DB 作为 Single Source of Truth
2. session_state 作为 LLM 上下文缓存
3. Webhook 只更新 DB
4. Agent 工具负责同步 session_state

工具说明：
- generate_image: 创建图片生成任务
- sync_pending_tasks: 同步所有未完成任务的最新状态（建议会话开始时调用）
- check_task_status: 查询单个任务状态并更新到 session_state
"""

import os
from dotenv import load_dotenv

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.deepseek import DeepSeek
from agno.tools.user_control_flow import UserControlFlowTools
from agno.os import AgentOS
from pkg.tools.image_generator import ImageGeneratorTools
from pkg.db.image_generation_db import ImageGenerationDB
from pkg.api.image_generation_api import register_image_generation_api

load_dotenv()
qnaigc_api_key = os.getenv("QNAIGC_API_KEY")

# 创建数据库实例（共享使用）
image_generation_db = ImageGenerationDB(db_path="tmp/image_generation.db")

# 创建图片生成工具实例
image_generator = ImageGeneratorTools(
    webhook_base_url="http://localhost:8000",  # 与AgentOS服务端口一致
    db=image_generation_db,  # 使用共享的数据库实例
)

# Agent 系统提示，引导 LLM 正确使用工具
SYSTEM_PROMPT = """你是一个图片生成助手，可以帮助用户生成图片。

## 可用工具

1. **generate_image** - 创建图片生成任务
   - 用户描述想要的图片时调用
   - 会自动从用户消息中提取 prompt

2. **sync_pending_tasks** - 同步所有未完成任务的状态
   - 建议在会话开始时调用，获取之前任务的最新状态
   - 用户询问"我的任务进度如何"时调用

3. **check_task_status** - 查询单个任务的最新状态
   - 用户询问特定任务进度时调用
   - 当 session_state 中任务状态不是 completed 但用户想使用图片时调用

## 使用指南

- 当用户开始新对话并提到之前的任务时，先调用 sync_pending_tasks
- 当用户想查看图片但任务状态显示未完成时，调用 check_task_status 获取最新状态
- 任务完成后，图片 URL 会在任务信息中显示
"""

agent = Agent(
    name="image_generator_agent",
    model=DeepSeek(
        id="deepseek/deepseek-v3.2-251201",
        api_key=qnaigc_api_key,
        base_url="https://api.qnaigc.com/v1",
    ),
    instructions=SYSTEM_PROMPT,
    tools=[UserControlFlowTools(), image_generator],
    markdown=True,
    db=SqliteDb(db_file="tmp/agno.db"),
    debug_level=2,
    debug_mode=True,
    enable_agentic_state=True,  # 启用 agentic state 以便工具可以更新 session_state
    add_session_state_to_context=True,  # 将 session_state 添加到 LLM 上下文
)
agent.run()
agent_os = AgentOS(
    agents=[agent],
)
app = agent_os.get_app()

# 注册图片生成任务相关的 API 端点
# 注意：Webhook 只更新数据库，不更新 session_state
register_image_generation_api(
    app=app,
    db=image_generation_db,
)


if __name__ == "__main__":
    agent_os.serve(app="state_agent:app", reload=True)
