"""
图片生成任务数据库工具

提供数据库模型和操作接口，方便在其他模块中使用
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, Column, String, DateTime, Text, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class ImageGenerationTask(Base):
    """图片生成任务数据库模型"""

    __tablename__ = "image_generation_tasks"

    id = Column(String, primary_key=True)  # task_id
    prompt = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    image_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    session_id = Column(String, nullable=True)  # 用于关联session
    run_id = Column(String, nullable=True)  # 用于关联agent的run，以便更新session_state


class ImageGenerationDB:
    """图片生成任务数据库操作类"""

    def __init__(self, db_path: str = "tmp/image_generation.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{self.db_path}")

        # 创建所有表
        Base.metadata.create_all(engine)

        # 检查并添加缺失的列（用于数据库迁移）
        inspector = inspect(engine)

        # 检查表是否存在
        if "image_generation_tasks" in inspector.get_table_names():
            # 获取现有列
            existing_columns = [
                col["name"] for col in inspector.get_columns("image_generation_tasks")
            ]

            # 检查并添加缺失的列
            with engine.connect() as conn:
                if "run_id" not in existing_columns:
                    conn.execute(
                        text(
                            "ALTER TABLE image_generation_tasks ADD COLUMN run_id VARCHAR"
                        )
                    )
                    conn.commit()
                    print("[ImageGenerationDB] 已添加缺失的 run_id 列到数据库")

        self.SessionLocal = sessionmaker(bind=engine)

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def create_task(
        self,
        task_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> ImageGenerationTask:
        """
        创建新任务

        Args:
            task_id: 任务ID
            prompt: 图片生成提示词
            session_id: 会话ID
            run_id: 运行ID

        Returns:
            创建的任务对象
        """
        db = self.get_session()
        try:
            task = ImageGenerationTask(
                id=task_id,
                prompt=prompt,
                status="pending",
                created_at=datetime.utcnow(),
                session_id=session_id,
                run_id=run_id,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_task(self, task_id: str) -> Optional[ImageGenerationTask]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在返回None
        """
        db = self.get_session()
        try:
            return db.query(ImageGenerationTask).filter_by(id=task_id).first()
        finally:
            db.close()

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        image_url: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[ImageGenerationTask]:
        """
        更新任务

        Args:
            task_id: 任务ID
            status: 状态
            image_url: 图片URL
            error_message: 错误信息
            completed_at: 完成时间

        Returns:
            更新后的任务对象，如果不存在返回None
        """
        db = self.get_session()
        try:
            task = db.query(ImageGenerationTask).filter_by(id=task_id).first()
            if not task:
                return None

            if status is not None:
                task.status = status
            if image_url is not None:
                task.image_url = image_url
            if error_message is not None:
                task.error_message = error_message
            if completed_at is not None:
                task.completed_at = completed_at

            db.commit()
            db.refresh(task)
            return task
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def list_tasks(
        self,
        status: Optional[str] = None,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, List[ImageGenerationTask]]:
        """
        查询任务列表

        Args:
            status: 状态过滤
            session_id: session_id过滤
            run_id: run_id过滤
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            (总数, 任务列表)
        """
        db = self.get_session()
        try:
            query = db.query(ImageGenerationTask)

            # 应用过滤条件
            if status:
                query = query.filter(ImageGenerationTask.status == status)
            if session_id:
                query = query.filter(ImageGenerationTask.session_id == session_id)
            if run_id:
                query = query.filter(ImageGenerationTask.run_id == run_id)

            # 获取总数
            total = query.count()

            # 应用分页和排序（按创建时间倒序）
            tasks = (
                query.order_by(ImageGenerationTask.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return total, tasks
        finally:
            db.close()

    def get_all_tasks(
        self,
        status: Optional[str] = None,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> tuple[int, List[ImageGenerationTask]]:
        """
        获取所有任务（不带分页限制）

        Args:
            status: 状态过滤
            session_id: session_id过滤
            run_id: run_id过滤

        Returns:
            (总数, 任务列表)
        """
        db = self.get_session()
        try:
            query = db.query(ImageGenerationTask)

            # 应用过滤条件
            if status:
                query = query.filter(ImageGenerationTask.status == status)
            if session_id:
                query = query.filter(ImageGenerationTask.session_id == session_id)
            if run_id:
                query = query.filter(ImageGenerationTask.run_id == run_id)

            # 获取总数
            total = query.count()

            # 获取所有任务（按创建时间倒序）
            tasks = query.order_by(ImageGenerationTask.created_at.desc()).all()

            return total, tasks
        finally:
            db.close()

    def task_to_dict(self, task: ImageGenerationTask) -> Dict[str, Any]:
        """
        将任务对象转换为字典

        Args:
            task: 任务对象

        Returns:
            任务字典
        """
        return {
            "task_id": task.id,
            "prompt": task.prompt,
            "status": task.status,
            "image_url": task.image_url,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
            "session_id": task.session_id,
            "run_id": task.run_id,
        }
