from datetime import datetime
from nicegui import ui
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from upload_data import engine, Task, User, create_task, update_task, create_subtask, toggle_subtask, delete_subtask, delete_task
from components.sidebar import create_sidebar

@ui.page('/tasks')
def tasks_page():
    # Hàm load dữ liệu từ database
    def get_data(search_term: str = None):
        with Session(engine) as session:
            statement = select(Task).options(joinedload(Task.links), joinedload(Task.subtasks)) # Load thêm links và subtasks
            statement = statement.where(Task.status != "Completed") # Loại bỏ các task đã hoàn thành
            statement = statement.where(Task.category != "Mail Responsed") # Loại bỏ email
            if search_term:
                statement = statement.where(Task.title.contains(search_term))
            results = session.exec(statement).unique().all()
            data = []
            for task in results:
                # Tính toán tiến độ subtasks
                total_sub = len(task.subtasks)
                completed_sub = sum(1 for s in task.subtasks if s.is_completed)
                progress = completed_sub / total_sub if total_sub > 0 else 0

                data.append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description or '',
                    'status': task.status,
                    'priority': task.priority,
                    'category': task.category,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '-',
                    'links': [l.url for l in task.links], # Lấy danh sách URL
                    'subtasks': [{'id': s.id, 'title': s.title, 'is_completed': s.is_completed, 'due_date': s.due_date} for s in task.subtasks],
                    'progress': progress,
                    'progress_label': f"{completed_sub}/{total_sub}" if total_sub > 0 else ""
                })
            return data

    # Biến table sẽ được gán sau khi khởi tạo UI
    table = None

    # Hàm mở popup (Dùng chung cho cả Thêm mới và Sửa)
    def open_task_dialog(task_data=None):
        # Kiểm tra xem đang ở chế độ Edit hay Create
        is_edit = task_data is not None
        dialog_title = 'Edit Task' if is_edit else 'Add New Task'
        
        # Danh sách link hiện tại (lấy từ DB nếu edit, hoặc rỗng)
        current_links = task_data['links'].copy() if is_edit else []
        # Subtasks chỉ xử lý trực tiếp khi đã có Task ID (tức là chế độ Edit)

        with ui.dialog() as dialog, ui.card().classes('w-[500px] p-6'):
            ui.label(dialog_title).classes('text-xl font-bold mb-2')
            
            with ui.column().classes('w-full gap-4'):
                # 1. Tên Task
                task_input = ui.input('Task Title', value=task_data['title'] if is_edit else '').classes('w-full').props('outlined dense autofocus')
                
                # 1.5. Notes / Description
                desc_input = ui.textarea('Notes / Description', value=task_data['description'] if is_edit else '').classes('w-full').props('outlined')
                
                # 2. Chọn ngày hết hạn (Due Date)
                default_date = task_data['due_date'] if is_edit and task_data['due_date'] != '-' else None
                with ui.input('Due Date', value=default_date).classes('w-full').props('outlined dense') as end_date_input:
                    with ui.menu() as menu:
                        ui.date().bind_value(end_date_input).on('input', menu.close)
                    with end_date_input.add_slot('append'):
                        ui.icon('event').classes('cursor-pointer')

                # 3. Priority
                priority_options = {1: 'High', 2: 'Medium', 3: 'Low'}
                default_priority = task_data['priority'] if is_edit else 2
                priority_input = ui.select(priority_options, value=default_priority, label='Priority').classes('w-full').props('outlined dense')
                
                # 4. Category (Phân loại)
                category_options = [
                    "Measurement Standards", 
                    "C&B Policy", 
                    "Productivity & Data", 
                    "Policy Consulting", 
                    "Ad-hoc Tasks",
                    "Mail Responsed"
                ]
                default_category = task_data['category'] if is_edit else "Ad-hoc Tasks"
                category_input = ui.select(category_options, value=default_category, label='Category').classes('w-full').props('outlined dense')

                # 5. Status (Chỉ hiện khi Edit)
                status_input = None
                if is_edit:
                    status_options = ['Pending', 'Completed', 'In Progress']
                    status_input = ui.select(status_options, value=task_data['status'], label='Status').classes('w-full').props('outlined dense')

                # 6. Attachments / Links
                ui.label('Attachments (SharePoint / Web)').classes('text-sm font-bold text-gray-600 mt-2')
                
                # Container chứa danh sách link
                links_container = ui.column().classes('w-full gap-1')

                def refresh_links_ui():
                    links_container.clear()
                    with links_container:
                        for url in current_links:
                            with ui.row().classes('w-full items-center justify-between bg-gray-50 px-2 py-1 rounded'):
                                ui.link(url, url).classes('text-xs text-blue-600 truncate max-w-[350px]').props('target=_blank')
                                ui.button(icon='close', on_click=lambda u=url: remove_link(u)).props('flat dense round size=xs color=red')

                def add_link():
                    val = link_input.value.strip()
                    if val:
                        if not val.startswith(('http://', 'https://')):
                            val = 'https://' + val
                        current_links.append(val)
                        link_input.value = ''
                        refresh_links_ui()
                
                def remove_link(url_to_remove):
                    if url_to_remove in current_links:
                        current_links.remove(url_to_remove)
                        refresh_links_ui()

                with ui.row().classes('w-full gap-2'):
                    link_input = ui.input('Paste link here...').classes('flex-1').props('outlined dense')
                    ui.button('Add', on_click=add_link).props('color=black dense')
                
                # Hiển thị danh sách ban đầu
                refresh_links_ui()

                # 7. Sub-tasks (Chỉ hiện khi Edit vì cần Task ID để lưu)
                if is_edit:
                    ui.separator().classes('my-2')
                    ui.label('Sub-tasks / Stages').classes('text-sm font-bold text-gray-600')
                    
                    # Tính toán tiến độ
                    subtasks_list = task_data.get('subtasks', [])
                    completed_count = sum(1 for s in subtasks_list if s['is_completed'])
                    total_count = len(subtasks_list)
                    progress_val = completed_count / total_count if total_count > 0 else 0
                    
                    progress_bar = ui.linear_progress(value=progress_val).classes('h-2 rounded-full color-green')
                    progress_label = ui.label(f'{completed_count}/{total_count} completed').classes('text-xs text-gray-400 mb-2')

                    subtasks_container = ui.column().classes('w-full gap-1')

                    def refresh_subtasks_ui():
                        # Cập nhật lại dữ liệu từ DB để đảm bảo đồng bộ
                        # (Trong thực tế nên tối ưu hơn, nhưng cách này an toàn nhất)
                        pass # UI được vẽ lại khi gọi hàm open_task_dialog lại hoặc update row

                    def add_new_subtask():
                        if subtask_input.value:
                            s_date = None
                            if sub_date_input.value:
                                s_date = datetime.strptime(sub_date_input.value, '%Y-%m-%d')
                            
                            create_subtask(task_data['id'], subtask_input.value, due_date=s_date)
                            subtask_input.value = ''
                            # Refresh dialog bằng cách đóng và mở lại (để load data mới)
                            # Hoặc cập nhật UI cục bộ. Ở đây ta chọn cách đơn giản: Update table rồi mở lại dialog
                            save(close_dialog=False) 

                    with subtasks_container:
                        for sub in subtasks_list:
                            with ui.row().classes('w-full items-center justify-between group'):
                                with ui.row().classes('items-center gap-2'):
                                    cb = ui.checkbox(sub['title'], value=sub['is_completed'], on_change=lambda e, sid=sub['id']: toggle_subtask(sid, e.value)).classes('text-sm')
                                    if sub['due_date']:
                                        d_val = sub['due_date']
                                        if isinstance(d_val, str):
                                            d_val = datetime.fromisoformat(d_val)
                                        ui.label(d_val.strftime('%d/%m')).classes('text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded')
                                
                                ui.button(icon='delete', on_click=lambda sid=sub['id']: [delete_subtask(sid), save(close_dialog=False)]).props('flat dense round size=xs color=grey').classes('opacity-0 group-hover:opacity-100 transition-opacity')

                    with ui.row().classes('w-full gap-2 mt-1'):
                        subtask_input = ui.input('Add a step...').classes('flex-1').props('outlined dense')
                        with ui.input('Date').classes('w-28').props('outlined dense') as sub_date_input:
                            with ui.menu() as menu:
                                ui.date().bind_value(sub_date_input).on('input', menu.close)
                        ui.button('Add', on_click=add_new_subtask).props('color=black dense')
            
            def save(close_dialog=True):
                if not task_input.value:
                    ui.notify('Please enter a task title', type='warning')
                    return
                
                # Chuyển đổi string ngày tháng sang datetime object
                fmt = '%Y-%m-%d'
                e_date = datetime.strptime(end_date_input.value, fmt) if end_date_input.value else None

                if is_edit:
                    # Logic Update
                    update_task(
                        task_id=task_data['id'],
                        title=task_input.value,
                        description=desc_input.value,
                        due_date=e_date,
                        priority=priority_input.value,
                        category=category_input.value,
                        status=status_input.value if status_input else None,
                        links=current_links
                    )
                    ui.notify('Task updated successfully!', type='positive')
                else:
                    # Logic Create
                    create_task(
                        title=task_input.value, 
                        description=desc_input.value, 
                        due_date=e_date, 
                        priority=priority_input.value, 
                        category=category_input.value, 
                        links=current_links
                    )
                    ui.notify('Task created successfully!', type='positive')

                # Refresh bảng
                table.rows = get_data()
                table.update()
                
                if close_dialog:
                    dialog.close()
                else:
                    # Nếu không đóng dialog (ví dụ khi thêm subtask), ta cần refresh lại nội dung dialog
                    # Cách đơn giản nhất: Tìm lại task data mới nhất và mở lại dialog
                    new_data = next((item for item in table.rows if item['id'] == task_data['id']), None)
                    if new_data:
                        dialog.close()
                        open_task_dialog(new_data)
            
            def delete_current_task():
                delete_task(task_data['id'])
                ui.notify('Task deleted successfully!', type='negative') # Thông báo màu đỏ
                table.rows = get_data() # Refresh lại bảng
                table.update()
                dialog.close()

            # Xử lý sự kiện Enter và Click nút
            task_input.on('keydown.enter', save)
            link_input.on('keydown.enter', add_link) # Enter ở ô link thì thêm link
            if is_edit:
                subtask_input.on('keydown.enter', add_new_subtask)
                sub_date_input.on('keydown.enter', add_new_subtask)
            
            # Footer của Dialog: Nút Delete (trái) - Cancel/Save (phải)
            with ui.row().classes('w-full justify-between mt-6'):
                if is_edit:
                    ui.button('Delete', on_click=delete_current_task).props('flat color=red icon=delete')
                else:
                    ui.label('') # Spacer nếu là tạo mới
                
                with ui.row().classes('gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
                    ui.button('Save', on_click=save).props('color=black')
        
        dialog.open()

    # --- GIAO DIỆN ĐỒNG BỘ VỚI DASHBOARD ---
    
    # Màu nền body
    ui.query('body').style('background-color: #f0f2f5;')

    # Khung chính (Main Container)
    with ui.row().classes('w-full max-w-[1280px] h-[850px] mx-auto mt-8 bg-[#f8fafc] rounded-[2rem] shadow-2xl overflow-hidden flex-nowrap border border-gray-200'):
        
        # --- 1. SIDEBAR ---
        create_sidebar('tasks')

        # --- 2. NỘI DUNG CHÍNH (Task Table) ---
        with ui.column().classes('flex-1 h-full p-10 overflow-y-auto bg-[#f8fafc] gap-0'):
            
            # Header của trang
            with ui.row().classes('w-full justify-between items-center mb-8'):
                with ui.column().classes('gap-1'):
                    ui.label('My Tasks').classes('text-[28px] font-extrabold text-gray-900 tracking-tight')
                    ui.label("Manage and track your work.").classes('text-sm text-gray-500 font-medium')
                
                with ui.row().classes('gap-4 items-center'):
                    # Ô tìm kiếm
                    search_field = ui.input(placeholder='Search by name...').props('outlined dense rounded').classes('w-64 bg-white')
                    with search_field.add_slot('prepend'):
                        ui.icon('search').classes('text-gray-400')
                    
                    # Nút thêm mới
                    ui.button('New Task', icon='add', on_click=lambda: open_task_dialog(None)).classes('rounded-xl px-4 py-2 font-bold shadow-lg')

            # Bảng dữ liệu (Đặt trong Card cho đẹp)
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 border border-gray-100 bg-white overflow-hidden').props('flat'):
                
                # Cấu hình cột
                columns = [
                    {'name': 'id', 'label': '#', 'field': 'id', 'sortable': True, 'align': 'left', 'classes': 'text-gray-400 font-bold'},
                    {'name': 'title', 'label': 'Task Name', 'field': 'title', 'sortable': True, 'align': 'left', 'classes': 'font-bold text-gray-800'},
                    {'name': 'category', 'label': 'Category', 'field': 'category', 'sortable': True, 'align': 'left'},
                    {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True, 'align': 'left'},
                    {'name': 'priority', 'label': 'Priority', 'field': 'priority', 'sortable': True, 'align': 'center'},
                    {'name': 'due_date', 'label': 'Due Date', 'field': 'due_date', 'sortable': True, 'align': 'right', 'classes': 'text-gray-500'},
                    {'name': 'progress', 'label': 'Progress', 'field': 'progress', 'align': 'left'},
                    {'name': 'links', 'label': 'Links', 'field': 'links', 'align': 'left'},
                ]
                
                # Render bảng
                table = ui.table(columns=columns, rows=get_data(), row_key='id').classes('w-full no-shadow')
                
                # Bắt sự kiện click vào dòng để Edit (e.args[1] chứa dữ liệu của dòng đó)
                table.on('rowClick', lambda e: open_task_dialog(e.args[1]))

                # Hàm xử lý khi nhập tìm kiếm
                def on_search():
                    table.rows = get_data(search_field.value)
                    table.update()
                
                # Gắn sự kiện nhập liệu (input) vào hàm xử lý
                search_field.on('input', on_search)

                # Custom style cho bảng (Quasar props)
                table.props('flat bordered=false square')
                
                # Slot tùy chỉnh hiển thị Category (Badge màu xám nhẹ)
                table.add_slot('body-cell-category', '''
                    <q-td :props="props">
                        <div class="bg-gray-100 text-gray-600 px-2 py-1 rounded text-[11px] font-bold inline-block border border-gray-200">
                            {{ props.value }}
                        </div>
                    </q-td>
                ''')

                # Slot tùy chỉnh hiển thị Status (Badge màu)
                table.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <div v-if="props.value == 'Completed'" class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold inline-block">
                            Completed
                        </div>
                        <div v-else-if="props.value == 'Pending'" class="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-bold inline-block">
                            Pending
                        </div>
                        <div v-else class="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-bold inline-block">
                            {{ props.value }}
                        </div>
                    </q-td>
                ''')

                # Slot tùy chỉnh hiển thị Progress Bar
                table.add_slot('body-cell-progress', '''
                    <q-td :props="props">
                        <div v-if="props.row.progress_label" class="w-24">
                            <div class="text-[10px] text-gray-500 mb-1 font-medium">{{ props.row.progress_label }}</div>
                            <q-linear-progress :value="props.value" size="6px" color="green" class="rounded-full" track-color="green-1" />
                        </div>
                        <div v-else class="text-gray-300 text-[10px] italic">No steps</div>
                    </q-td>
                ''')

                # Slot tùy chỉnh hiển thị Links (link1, link2...)
                table.add_slot('body-cell-links', '''
                    <q-td :props="props">
                        <div class="flex gap-1 flex-wrap">
                            <a v-for="(link, index) in props.value" :key="index" :href="link" target="_blank" @click.stop class="text-blue-600 hover:underline text-xs bg-blue-50 px-2 py-1 rounded border border-blue-100">
                                link{{ index + 1 }}
                            </a>
                        </div>
                    </q-td>
                ''')