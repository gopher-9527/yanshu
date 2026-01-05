"""
图片生成任务API模块

提供独立的API端点：
1. Webhook 回调 - 只负责更新数据库
2. 任务查询 API - 用于外部查询任务状态

设计原则：
- Webhook 只更新数据库，不尝试更新 session_state
- session_state 的更新由 Agent 工具（sync_pending_tasks, check_task_status）负责
"""

from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from pkg.db.image_generation_db import ImageGenerationDB


# ==================== 请求和响应模型 ====================


class ImageGenerationCallback(BaseModel):
    """Webhook回调请求模型

    注意：此回调只更新数据库，不更新 session_state
    """

    task_id: str
    status: str
    image_url: str
    completed_at: str
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    """任务响应模型"""

    task_id: str
    prompt: str
    status: str
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    session_id: Optional[str] = None
    run_id: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应模型"""

    total: int
    tasks: List[TaskResponse]


class WebhookResponse(BaseModel):
    """Webhook响应模型"""

    success: bool
    message: str
    task_id: str


# ==================== API 注册函数 ====================


def register_image_generation_api(
    app: FastAPI,
    db: ImageGenerationDB,
    agent=None,  # 保留参数兼容性，但不再使用
):
    """
    注册图片生成任务相关的API端点

    Args:
        app: FastAPI应用实例
        db: 数据库实例
        agent: Agent实例（保留兼容性，不再使用）
    """

    # ==================== Webhook 回调端点 ====================

    @app.post("/webhook/image-generation-callback", response_model=WebhookResponse)
    async def image_generation_callback(callback: ImageGenerationCallback):
        """处理图片生成完成的 Webhook 回调

        此端点只负责更新数据库中的任务状态。
        session_state 的更新由 Agent 工具负责（sync_pending_tasks 或 check_task_status）。

        Args:
            callback: 回调数据，包含任务ID、状态、图片URL等

        Returns:
            处理结果
        """
        try:
            # 解析完成时间
            try:
                completed_at = datetime.fromisoformat(
                    callback.completed_at.replace("Z", "+00:00")
                )
            except ValueError:
                completed_at = datetime.utcnow()

            # 更新数据库
            task = db.update_task(
                task_id=callback.task_id,
                status=callback.status,
                image_url=callback.image_url,
                error_message=callback.error_message,
                completed_at=completed_at,
            )

            if not task:
                raise HTTPException(
                    status_code=404, detail=f"任务 {callback.task_id} 不存在"
                )

            print(f"[Webhook] 任务状态已更新: {callback.task_id} -> {callback.status}")

            return WebhookResponse(
                success=True,
                message=f"任务 {callback.task_id} 状态已更新为 {callback.status}",
                task_id=callback.task_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"[Webhook] 处理回调失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"处理回调失败: {str(e)}")

    # ==================== 任务查询 API ====================

    @app.get("/api/tasks/{task_id}", response_model=TaskResponse)
    async def get_task(task_id: str):
        """查询单个任务的状态

        Args:
            task_id: 任务ID

        Returns:
            任务详细信息
        """
        try:
            task = db.get_task(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

            return TaskResponse(**db.task_to_dict(task))
        except HTTPException:
            raise
        except Exception as e:
            print(f"[API] 查询任务失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询任务失败: {str(e)}")

    @app.get("/api/tasks", response_model=TaskListResponse)
    async def list_tasks(
        status: Optional[str] = Query(
            None, description="按状态过滤: pending, processing, completed, failed"
        ),
        session_id: Optional[str] = Query(None, description="按session_id过滤"),
        run_id: Optional[str] = Query(None, description="按run_id过滤"),
        limit: int = Query(100, ge=1, le=1000, description="返回记录数限制"),
        offset: int = Query(0, ge=0, description="偏移量"),
    ):
        """查询任务列表（带分页）

        Args:
            status: 任务状态过滤（可选）
            session_id: session_id过滤（可选）
            run_id: run_id过滤（可选）
            limit: 返回记录数限制，默认100，最大1000
            offset: 偏移量，默认0

        Returns:
            任务列表和总数
        """
        try:
            total, tasks = db.list_tasks(
                status=status,
                session_id=session_id,
                run_id=run_id,
                limit=limit,
                offset=offset,
            )

            task_list = [TaskResponse(**db.task_to_dict(task)) for task in tasks]

            return TaskListResponse(total=total, tasks=task_list)
        except Exception as e:
            print(f"[API] 查询任务列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询任务列表失败: {str(e)}")

    @app.get("/api/tasks/all", response_model=TaskListResponse)
    async def get_all_tasks(
        status: Optional[str] = Query(
            None, description="按状态过滤: pending, processing, completed, failed"
        ),
        session_id: Optional[str] = Query(None, description="按session_id过滤"),
        run_id: Optional[str] = Query(None, description="按run_id过滤"),
    ):
        """查询所有任务（不带分页限制）

        Args:
            status: 任务状态过滤（可选）
            session_id: session_id过滤（可选）
            run_id: run_id过滤（可选）

        Returns:
            所有任务列表和总数
        """
        try:
            total, tasks = db.get_all_tasks(
                status=status,
                session_id=session_id,
                run_id=run_id,
            )

            task_list = [TaskResponse(**db.task_to_dict(task)) for task in tasks]

            return TaskListResponse(total=total, tasks=task_list)
        except Exception as e:
            print(f"[API] 查询所有任务失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询所有任务失败: {str(e)}")

    # ==================== 健康检查 ====================

    @app.get("/api/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy", "service": "image-generation-api"}
