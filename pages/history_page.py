from datetime import datetime
from nicegui import ui
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from upload_data import engine, Task, create_task, update_task, create_subtask, toggle_subtask, delete_subtask
from components.sidebar import create_sidebar

@ui.page('/history')
def history_page():
    # --- LOGIC DATA ---
    def get_completed_data(search_term: str = None):
        with Session(engine) as session:
            # Lọc chỉ lấy status = 'Completed'
            statement = select(Task).options(joinedload(Task.links), joinedload(Task.subtasks)).where(Task.status == "Completed", Task.category != "Mail Responsed")
            
            if search_term:
                statement = statement.where(Task.title.contains(search_term))
            
            # Sắp xếp task mới nhất lên đầu
            statement = statement.order_by(Task.due_date.desc())
            
            results = session.exec(statement).unique().all()
            data = []
            for task in results:
                total_sub = len(task.subtasks)
                completed_sub = sum(1 for s in task.subtasks if s.is_completed)
                progress = completed_sub / total_sub if total_sub > 0 else 0

                data.append({
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'priority': task.priority,
                    'category': task.category,
                    'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else '-',
                    'links': [l.url for l in task.links],
                    'subtasks': [{'id': s.id, 'title': s.title, 'is_completed': s.is_completed, 'due_date': s.due_date} for s in task.subtasks],
                    'progress': progress,
                    'progress_label': f"{completed_sub}/{total_sub}" if total_sub > 0 else ""
                })
            return data

    # --- UI SETUP ---
    ui.query('body').style('background-color: #f0f2f5;')

    # Khung chính
    with ui.row().classes('w-full max-w-[1280px] h-[850px] mx-auto mt-8 bg-[#f8fafc] rounded-[2rem] shadow-2xl overflow-hidden flex-nowrap border border-gray-200'):
        
        # --- 1. SIDEBAR ---
        create_sidebar('history')

        # --- 2. NỘI DUNG CHÍNH ---
        with ui.column().classes('flex-1 h-full p-10 overflow-y-auto bg-[#f8fafc] gap-0'):
            
            # Header
            with ui.row().classes('w-full justify-between items-center mb-8'):
                with ui.column().classes('gap-1'):
                    ui.label('Task History').classes('text-[28px] font-extrabold text-gray-900 tracking-tight')
                    ui.label("Archive of completed tasks.").classes('text-sm text-gray-500 font-medium')
                
                with ui.row().classes('gap-4 items-center'):
                    search_field = ui.input(placeholder='Search history...').props('outlined dense rounded').classes('w-64 bg-white')
                    with search_field.add_slot('prepend'):
                        ui.icon('search').classes('text-gray-400')

            # Bảng dữ liệu
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 border border-gray-100 bg-white overflow-hidden').props('flat'):
                
                columns = [
                    {'name': 'id', 'label': '#', 'field': 'id', 'sortable': True, 'align': 'left', 'classes': 'text-gray-400 font-bold'},
                    {'name': 'title', 'label': 'Task Name', 'field': 'title', 'sortable': True, 'align': 'left', 'classes': 'font-bold text-gray-800 ellipsis', 'style': 'max-width: 300px'},
                    {'name': 'category', 'label': 'Category', 'field': 'category', 'sortable': True, 'align': 'left'},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True, 'align': 'left'},
                    {'name': 'completed_at', 'label': 'Completed At', 'field': 'completed_at', 'sortable': True, 'align': 'right', 'classes': 'text-gray-500'},
                    {'name': 'links', 'label': 'Links', 'field': 'links', 'align': 'left'},
                ]
                
                table = ui.table(columns=columns, rows=get_completed_data(), row_key='id', pagination=10).classes('w-full no-shadow')
                
                # Search logic
                def on_search():
                    table.rows = get_completed_data(search_field.value)
                    table.update()
                search_field.on('input', on_search)

                # Custom slots
                table.props('flat bordered=false square')
                
                table.add_slot('body-cell-category', '''
                    <q-td :props="props">
                        <div class="bg-gray-100 text-gray-600 px-2 py-1 rounded text-[11px] font-bold inline-block border border-gray-200">
                            {{ props.value }}
                        </div>
                    </q-td>
                ''')

                table.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <div class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold inline-block">
                            Completed
                        </div>
                    </q-td>
                ''')

                table.add_slot('body-cell-links', '''
                    <q-td :props="props">
                        <div class="flex gap-1 flex-wrap">
                            <a v-for="(link, index) in props.value" :key="index" :href="link" target="_blank" @click.stop class="text-blue-600 hover:underline text-xs bg-blue-50 px-2 py-1 rounded border border-blue-100">
                                link{{ index + 1 }}
                            </a>
                        </div>
                    </q-td>
                ''')
