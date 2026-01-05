"""
异步图片生成工具

实现功能：
1. 生成时记录到db和session_state
2. 生成完成后通过webhook更新db
3. 提供工具同步session_state中未完成任务的最新状态
4. 提供工具查询单个任务状态并更新到session_state

设计原则：
- DB 作为 Single Source of Truth
- session_state 只是缓存，用于 LLM 上下文
- Webhook 只负责更新 DB，不尝试更新 session_state
- session_state 的更新由用户主动查询触发
"""

import asyncio
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

from agno.tools import Toolkit
from pkg.db.image_generation_db import ImageGenerationDB

# session_state 中保留的最大任务数量
MAX_TASKS_IN_SESSION_STATE = 20


class ImageGeneratorTools(Toolkit):
    """图片生成工具集

    提供以下工具：
    1. generate_image - 创建图片生成任务
    2. sync_pending_tasks - 同步所有未完成任务的最新状态（建议在会话开始时调用）
    3. check_task_status - 查询单个任务的最新状态
    """

    def __init__(
        self,
        db_path: str = "tmp/image_generation.db",
        webhook_base_url: str = "http://localhost:8000",
        db: Optional[ImageGenerationDB] = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            name="ImageGeneratorTools",
            tools=[
                self.generate_image,
                self.sync_pending_tasks,
                self.check_task_status,
            ],
            *args,
            **kwargs,
        )
        self.webhook_base_url = webhook_base_url
        # 使用传入的db实例，或创建新的
        self.db = db if db is not None else ImageGenerationDB(db_path=db_path)

    # ==================== Session State 管理方法 ====================

    def _get_tasks_from_session_state(
        self, session_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从 session_state 获取任务列表"""
        if session_state is None:
            return []
        return session_state.get("image_generation_tasks", [])

    def _update_task_in_session_state(
        self,
        session_state: Dict[str, Any],
        task_info: Dict[str, Any],
    ) -> None:
        """安全地更新单个任务状态（合并策略，非覆盖）

        Args:
            session_state: session state 字典
            task_info: 任务信息，必须包含 task_id
        """
        if session_state is None:
            return

        if "image_generation_tasks" not in session_state:
            session_state["image_generation_tasks"] = []

        tasks = session_state["image_generation_tasks"]
        task_id = task_info.get("task_id")

        # 查找并更新现有任务
        for i, task in enumerate(tasks):
            if task.get("task_id") == task_id:
                # 合并更新，保留原有字段
                tasks[i] = {**task, **task_info}
                return

        # 如果任务不存在，添加到列表
        tasks.append(task_info)

    def _cleanup_old_tasks(self, session_state: Dict[str, Any]) -> None:
        """清理过期的任务，只保留最近的 N 个

        清理策略：
        1. 保留所有未完成的任务（pending, processing）
        2. 已完成/失败的任务按时间排序，只保留最近的
        3. 总数不超过 MAX_TASKS_IN_SESSION_STATE
        """
        if session_state is None:
            return

        tasks = session_state.get("image_generation_tasks", [])
        if len(tasks) <= MAX_TASKS_IN_SESSION_STATE:
            return

        # 分离未完成和已完成的任务
        pending_tasks = [
            t for t in tasks if t.get("status") in ("pending", "processing")
        ]
        completed_tasks = [
            t for t in tasks if t.get("status") not in ("pending", "processing")
        ]

        # 对已完成任务按创建时间排序（最新的在前）
        completed_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # 计算可以保留多少已完成任务
        remaining_slots = MAX_TASKS_IN_SESSION_STATE - len(pending_tasks)
        kept_completed = completed_tasks[: max(0, remaining_slots)]

        # 合并并更新
        session_state["image_generation_tasks"] = pending_tasks + kept_completed

        cleaned_count = len(tasks) - len(session_state["image_generation_tasks"])
        if cleaned_count > 0:
            print(f"[ImageGenerator] 清理了 {cleaned_count} 个旧任务")

    # ==================== 工具方法 ====================

    def _extract_prompt_from_context(
        self, run_context: Any = None, agent: Any = None
    ) -> Optional[str]:
        """从用户对话上下文中提取图片生成提示词

        Args:
            run_context: agno RunContext实例
            agent: agno Agent实例

        Returns:
            提取的提示词，如果无法提取则返回None
        """
        # 方法1: 从run_context中获取用户消息
        if run_context:
            # 尝试获取消息历史
            if hasattr(run_context, "messages") and run_context.messages:
                # 查找最后一条用户消息
                for message in reversed(run_context.messages):
                    if hasattr(message, "role") and message.role == "user":
                        if hasattr(message, "content"):
                            content = message.content
                            if isinstance(content, str):
                                return content.strip()
                            elif isinstance(content, list):
                                # 处理多部分内容
                                text_parts = [
                                    item.get("text", "")
                                    for item in content
                                    if isinstance(item, dict) and "text" in item
                                ]
                                if text_parts:
                                    return " ".join(text_parts).strip()

            # 尝试获取当前用户输入
            if hasattr(run_context, "user_message"):
                user_msg = run_context.user_message
                if isinstance(user_msg, str):
                    return user_msg.strip()
                elif hasattr(user_msg, "content"):
                    content = user_msg.content
                    if isinstance(content, str):
                        return content.strip()

            # 尝试从run_context的其他属性获取
            if hasattr(run_context, "current_message"):
                msg = run_context.current_message
                if hasattr(msg, "content"):
                    content = msg.content
                    if isinstance(content, str):
                        return content.strip()

        # 方法2: 从agent中获取当前消息
        if agent:
            # 尝试获取agent的当前运行消息
            if hasattr(agent, "_current_user_message"):
                msg = agent._current_user_message
                if isinstance(msg, str):
                    return msg.strip()
                elif hasattr(msg, "content"):
                    return str(msg.content).strip()

        return None

    def generate_image(
        self,
        prompt: Optional[str] = None,
        task_id: Optional[str] = None,
        agent: Any = None,
        session_state: Dict[str, Any] = None,
        run_context: Any = None,
    ) -> str:
        """创建图片生成任务（异步执行）

        创建一个新的图片生成任务，任务会在后台异步执行。
        任务创建后会立即记录到数据库和 session_state 中。

        Args:
            prompt: 图片生成提示词。如果为空，将从用户对话中自动获取
            task_id: 任务ID。如果为空，将自动生成UUID
            agent: agno Agent实例
            session_state: 当前会话状态字典
            run_context: agno RunContext实例

        Returns:
            返回任务已提交的消息，包含任务ID
        """
        if session_state is None:
            session_state = {}

        # 如果prompt为空，尝试从用户对话中获取
        if not prompt:
            prompt = self._extract_prompt_from_context(run_context, agent)
            if not prompt:
                return "错误：无法获取图片生成提示词。请提供prompt参数或在对话中描述要生成的图片。"

        # 如果task_id为空，自动生成UUID
        if not task_id:
            task_id = str(uuid.uuid4())

        # 获取run_id（如果可用）
        run_id = None
        if run_context and hasattr(run_context, "run_id"):
            run_id = run_context.run_id
        elif agent and hasattr(agent, "_current_run_id"):
            run_id = agent._current_run_id
        elif session_state and "run_id" in session_state:
            run_id = session_state.get("run_id")

        # 1. 记录生成记录到数据库
        try:
            # 检查任务是否已存在
            existing_task = self.db.get_task(task_id)
            if existing_task:
                return f"任务 {task_id} 已存在，状态: {existing_task.status}"

            # 创建新任务
            self.db.create_task(
                task_id=task_id,
                prompt=prompt,
                session_id=session_state.get("session_id") if session_state else None,
                run_id=run_id,
            )

            # 2. 记录到session_state（使用安全的更新方法）
            task_info = {
                "task_id": task_id,
                "prompt": prompt,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            self._update_task_in_session_state(session_state, task_info)

            # 清理旧任务
            self._cleanup_old_tasks(session_state)

            # 3. 启动异步生成任务（在后台线程中运行）
            def run_async_task():
                """在独立的事件循环中运行异步任务"""
                try:
                    # 创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        self._async_generate_image(
                            task_id=task_id,
                            prompt=prompt,
                        )
                    )
                except Exception as e:
                    print(f"[ImageGenerator] 异步任务执行失败: {str(e)}")
                finally:
                    loop.close()

            # 在后台线程中运行
            thread = threading.Thread(target=run_async_task, daemon=True)
            thread.start()

            return f"图片生成任务已提交，任务ID: {task_id}。任务正在后台处理中，您可以稍后使用 check_task_status 工具查询进度。"

        except Exception as e:
            return f"创建任务失败: {str(e)}"

    def sync_pending_tasks(
        self,
        session_state: Dict[str, Any] = None,
    ) -> str:
        """同步所有未完成任务的最新状态到 session_state

        **建议在以下场景调用此工具：**
        1. 会话开始时，同步之前未完成任务的最新状态
        2. 用户询问"我的任务进度如何"等问题时
        3. 需要获取所有任务最新状态时

        此工具会从数据库查询所有未完成任务（pending/processing）的最新状态，
        并更新到 session_state 中。

        Args:
            session_state: 当前会话状态字典

        Returns:
            同步结果摘要
        """
        if session_state is None:
            return "错误：session_state 不可用"

        try:
            # 获取 session_state 中的任务列表
            tasks_in_state = self._get_tasks_from_session_state(session_state)

            # 找出所有未完成的任务ID
            pending_task_ids = [
                t.get("task_id")
                for t in tasks_in_state
                if t.get("status") in ("pending", "processing") and t.get("task_id")
            ]

            if not pending_task_ids:
                return "没有需要同步的未完成任务"

            # 从数据库查询这些任务的最新状态
            updated_count = 0
            completed_count = 0
            still_pending_count = 0

            for task_id in pending_task_ids:
                db_task = self.db.get_task(task_id)
                if db_task:
                    task_dict = self.db.task_to_dict(db_task)
                    self._update_task_in_session_state(session_state, task_dict)
                    updated_count += 1

                    if db_task.status == "completed":
                        completed_count += 1
                    elif db_task.status in ("pending", "processing"):
                        still_pending_count += 1

            # 清理旧任务
            self._cleanup_old_tasks(session_state)

            result_parts = [f"已同步 {updated_count} 个任务的状态"]
            if completed_count > 0:
                result_parts.append(f"{completed_count} 个已完成")
            if still_pending_count > 0:
                result_parts.append(f"{still_pending_count} 个仍在处理中")

            return "。".join(result_parts) + "。"

        except Exception as e:
            return f"同步任务状态失败: {str(e)}"

    def check_task_status(
        self,
        task_id: str,
        session_state: Dict[str, Any] = None,
    ) -> str:
        """查询单个任务的最新状态并更新到 session_state

        **建议在以下场景调用此工具：**
        1. 用户询问特定任务的进度时
        2. 需要使用图片但 session_state 中该任务状态不是 completed 时
        3. 想要获取任务的详细信息（如图片URL）时

        此工具会从数据库查询任务的最新状态，并更新到 session_state 中。

        Args:
            task_id: 任务ID
            session_state: 当前会话状态字典

        Returns:
            任务的最新状态信息
        """
        if not task_id:
            return "错误：请提供任务ID"

        try:
            # 从数据库查询最新状态
            db_task = self.db.get_task(task_id)

            if not db_task:
                return f"任务 {task_id} 不存在"

            task_dict = self.db.task_to_dict(db_task)

            # 更新到 session_state
            if session_state is not None:
                self._update_task_in_session_state(session_state, task_dict)

            # 构建返回信息
            status_info = f"任务ID: {task_id}\n"
            status_info += f"状态: {task_dict['status']}\n"
            status_info += f"提示词: {task_dict['prompt']}\n"

            if task_dict.get("image_url"):
                status_info += f"图片URL: {task_dict['image_url']}\n"

            if task_dict.get("error_message"):
                status_info += f"错误信息: {task_dict['error_message']}\n"

            if task_dict.get("created_at"):
                status_info += f"创建时间: {task_dict['created_at']}\n"

            if task_dict.get("completed_at"):
                status_info += f"完成时间: {task_dict['completed_at']}\n"

            return status_info

        except Exception as e:
            return f"查询任务状态失败: {str(e)}"

    # ==================== 内部异步方法 ====================

    async def _async_generate_image(
        self,
        task_id: str,
        prompt: str,
    ):
        """异步生成图片的模拟实现

        注意：此方法只更新数据库，不尝试更新 session_state。
        session_state 的更新由用户主动调用 check_task_status 或 sync_pending_tasks 触发。
        """
        try:
            # 更新状态为processing
            task = self.db.get_task(task_id)
            if not task:
                return

            self.db.update_task(task_id=task_id, status="processing")

            # 模拟图片生成过程（实际应该调用真实的图片生成API）
            print(f"[ImageGenerator] 开始生成图片，任务ID: {task_id}, 提示词: {prompt}")
            await asyncio.sleep(5)  # 模拟耗时操作（改为5秒便于测试）

            # 模拟生成结果
            image_url = f"https://example.com/generated-images/{task_id}.png"

            print(
                f"[ImageGenerator] 图片生成完成，任务ID: {task_id}, 图片URL: {image_url}"
            )

            # 调用 webhook 更新数据库（webhook 只更新 DB）
            await self._call_webhook(task_id, image_url)

        except Exception as e:
            print(f"[ImageGenerator] 生成图片失败，任务ID: {task_id}, 错误: {str(e)}")
            self.db.update_task(task_id=task_id, status="failed", error_message=str(e))

    async def _call_webhook(
        self,
        task_id: str,
        image_url: str,
    ):
        """调用webhook回调，更新数据库中的任务状态

        注意：Webhook 只负责更新数据库，不尝试更新 session_state。
        """
        import httpx

        webhook_url = f"{self.webhook_base_url}/webhook/image-generation-callback"
        payload = {
            "task_id": task_id,
            "status": "completed",
            "image_url": image_url,
            "completed_at": datetime.utcnow().isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                if response.status_code == 200:
                    print(f"[ImageGenerator] Webhook回调成功，任务ID: {task_id}")
                else:
                    print(
                        f"[ImageGenerator] Webhook回调失败，状态码: {response.status_code}"
                    )
                    # 如果 webhook 失败，直接更新数据库
                    self.db.update_task(
                        task_id=task_id,
                        status="completed",
                        image_url=image_url,
                        completed_at=datetime.utcnow(),
                    )
        except httpx.ConnectError as e:
            print(f"[ImageGenerator] Webhook连接失败: {e}")
            # 直接更新数据库作为后备
            self.db.update_task(
                task_id=task_id,
                status="completed",
                image_url=image_url,
                completed_at=datetime.utcnow(),
            )
        except httpx.TimeoutException as e:
            print(f"[ImageGenerator] Webhook请求超时: {e}")
            self.db.update_task(
                task_id=task_id,
                status="completed",
                image_url=image_url,
                completed_at=datetime.utcnow(),
            )
        except Exception as e:
            print(f"[ImageGenerator] Webhook回调异常: {str(e)}")
            self.db.update_task(
                task_id=task_id,
                status="completed",
                image_url=image_url,
                completed_at=datetime.utcnow(),
            )

    # ==================== 兼容性方法（保留旧接口） ====================

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态（仅返回数据库中的状态，不更新 session_state）

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息字典
        """
        task = self.db.get_task(task_id)
        if not task:
            return {"error": f"任务 {task_id} 不存在"}

        return self.db.task_to_dict(task)
