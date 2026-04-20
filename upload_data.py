from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import joinedload
from sqlalchemy import case
from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship, func, or_

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: str | None = None

    tasks: List["Task"] = Relationship(back_populates="assignee")


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None

    tasks: List["Task"] = Relationship(back_populates="project")


class TaskLink(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str
    task_id: int = Field(foreign_key="task.id")
    task: "Task" = Relationship(back_populates="links")


class SubTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    is_completed: bool = Field(default=False)
    due_date: datetime | None = None
    task_id: int = Field(foreign_key="task.id")
    task: "Task" = Relationship(back_populates="subtasks")


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str | None = None
    status: str = Field(default="Pending")
    priority: int = Field(default=2)
    category: str = Field(default="Ad-hoc Tasks") # Thêm trường Category
    start_date: datetime | None = None
    due_date: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None # Thời điểm hoàn thành task
    outlook_id: str | None = Field(default=None, index=True) # ID của email để tránh trùng lặp

    project_id: int | None = Field(default=None, foreign_key="project.id")
    project: Project | None = Relationship(back_populates="tasks")

    assignee_id: int | None = Field(default=None, foreign_key="user.id")
    assignee: User | None = Relationship(back_populates="tasks")

    links: List["TaskLink"] = Relationship(back_populates="task")
    subtasks: List["SubTask"] = Relationship(back_populates="task")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_tasks_by_user_id(user_id: int) -> List[Task]:
    with Session(engine) as session:
        statement = select(Task).where(Task.assignee_id == user_id)
        results = session.exec(statement).all()
        return results


def create_task(
    title: str,
    description: str | None = None,
    status: str = "Pending",
    priority: int = 2,
    category: str = "Ad-hoc Tasks",
    due_date: datetime | None = None,
    project_id: int | None = None,
    assignee_id: int | None = None,
    links: List[str] | None = None,
    outlook_id: str | None = None,
) -> Task:
    with Session(engine) as session:
        task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            category=category,
            start_date=datetime.now(), # Mặc định start_date là thời điểm tạo
            due_date=due_date,
            completed_at=datetime.now() if status == "Completed" else None,
            project_id=project_id,
            assignee_id=assignee_id,
            outlook_id=outlook_id,
        )
        
        if links:
            for url in links:
                task.links.append(TaskLink(url=url))
                
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


# --- CÁC HÀM XỬ LÝ SUB-TASK ---

def create_subtask(task_id: int, title: str, due_date: datetime | None = None) -> SubTask:
    with Session(engine) as session:
        subtask = SubTask(title=title, task_id=task_id, due_date=due_date)
        session.add(subtask)
        session.commit()
        session.refresh(subtask)
        return subtask

def toggle_subtask(subtask_id: int, is_completed: bool):
    with Session(engine) as session:
        subtask = session.get(SubTask, subtask_id)
        if subtask:
            subtask.is_completed = is_completed
            session.add(subtask)
            session.commit()

def delete_subtask(subtask_id: int):
    with Session(engine) as session:
        subtask = session.get(SubTask, subtask_id)
        if subtask:
            session.delete(subtask)
            session.commit()


# --- CÁC HÀM MỚI CHO DASHBOARD ---

def get_dashboard_stats():
    """Lấy số liệu thống kê cho 4 thẻ trên cùng."""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    now = datetime.now()

    with Session(engine) as session:
        # Completed Today: Đã xong VÀ thời gian xong nằm trong hôm nay
        total_completed = session.exec(select(func.count(Task.id)).where(
            Task.status == "Completed",
            Task.completed_at >= today_start,
            Task.completed_at < today_end,
            Task.category != "Mail Responsed"
        )).one()

        # Pending Today: Chưa xong VÀ hạn chót là hôm nay
        total_pending = session.exec(select(func.count(Task.id)).where(
            Task.status == "Pending",
            Task.due_date >= today_start,
            Task.due_date < today_end,
            Task.category != "Mail Responsed"
        )).one()
        
        # Overdue: Chưa xong và due_date < hiện tại
        total_overdue = session.exec(select(func.count(Task.id)).where(Task.status != "Completed", Task.due_date < now, Task.category != "Mail Responsed")).one()
        
        # Active Today: Đang làm VÀ hạn chót là hôm nay
        total_active = session.exec(select(func.count(Task.id)).where(
            Task.status == "In Progress",
            Task.due_date >= today_start,
            Task.due_date < today_end,
            Task.category != "Mail Responsed"
        )).one()
        
        return {
            "completed": total_completed,
            "pending": total_pending,
            "overdue": total_overdue,
            "active": total_active
        }

def get_overdue_tasks_list():
    """Lấy danh sách task quá hạn."""
    now = datetime.now()
    with Session(engine) as session:
        statement = select(Task).options(joinedload(Task.project)).where(
            Task.status != "Completed", 
            Task.due_date < now,
            Task.category != "Mail Responsed"
        ).order_by(Task.due_date)
        return session.exec(statement).all()

def get_inprogress_tasks_list():
    """Lấy danh sách task đang thực hiện."""
    with Session(engine) as session:
        statement = select(Task).options(joinedload(Task.project)).where(Task.status == "In Progress", Task.category != "Mail Responsed").order_by(Task.due_date)
        return session.exec(statement).all()

def get_pending_tasks_list():
    """Lấy danh sách task đang chờ."""
    with Session(engine) as session:
        statement = select(Task).options(joinedload(Task.project)).where(Task.status == "Pending", Task.category != "Mail Responsed").order_by(Task.due_date)
        return session.exec(statement).all()

def get_chart_data():
    """Lấy dữ liệu cho biểu đồ."""
    with Session(engine) as session:
        # Pie Chart: Tỷ trọng theo Category
        pie_stmt = select(Task.category, func.count(Task.id)).where(Task.category != "Mail Responsed").group_by(Task.category)
        pie_results = session.exec(pie_stmt).all()
        pie_data = [{"name": cat, "y": count} for cat, count in pie_results]

        # Column Chart: Completed vs Total theo Category
        col_stmt = select(
            Task.category,
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "Completed", 1), else_=0)).label("completed")
        ).where(Task.category != "Mail Responsed").group_by(Task.category)
        col_results = session.exec(col_stmt).all()
        
        categories = []
        total_data = []
        completed_data = []
        for cat, total, completed in col_results:
            categories.append(cat)
            total_data.append(total)
            completed_data.append(completed if completed else 0)
            
        return {
            "pie_data": pie_data,
            "column_data": {
                "categories": categories,
                "total": total_data,
                "completed": completed_data
            }
        }


def update_task_status(task_id: int, new_status: str) -> Task | None:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return None
        task.status = new_status
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    category: str | None = None,
    due_date: datetime | None = None,
    links: List[str] | None = None,
) -> Task | None:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return None
        
        if title: task.title = title
        if description is not None: task.description = description
        if status:
            # Nếu chuyển sang Completed -> Ghi nhận thời gian
            if status == "Completed" and task.status != "Completed":
                task.completed_at = datetime.now()
            # Nếu mở lại task (không còn Completed) -> Xóa thời gian completed
            elif status != "Completed":
                task.completed_at = None
            task.status = status
        if priority: task.priority = priority
        if category: task.category = category
        if due_date: task.due_date = due_date
        
        if links is not None:
            # Xóa các link cũ
            for link in task.links:
                session.delete(link)
            # Thêm link mới
            for url in links:
                task.links.append(TaskLink(url=url))
        
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task:
            # Xóa các link và subtask liên quan trước để tránh lỗi hoặc rác data
            for link in task.links:
                session.delete(link)
            for sub in task.subtasks:
                session.delete(sub)
            session.delete(task)
            session.commit()

def migrate_outlook_tasks():
    """Cập nhật các task tạo từ email cũ sang danh mục Mail Responsed."""
    with Session(engine) as session:
        tasks = session.exec(select(Task).where(Task.outlook_id != None)).all()
        for task in tasks:
            if task.category != "Mail Responsed":
                task.category = "Mail Responsed"
                session.add(task)
        session.commit()