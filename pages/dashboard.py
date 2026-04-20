from nicegui import ui
from components.sidebar import create_sidebar
from components.cards import stat_card, project_row
from upload_data import get_dashboard_stats, get_overdue_tasks_list, get_inprogress_tasks_list, get_pending_tasks_list, get_chart_data
from datetime import datetime
from outlook_service import sync_outlook_tasks
from components.sidebar import create_sidebar



@ui.page('/')
def main_dashboard():
    # Kích hoạt đồng bộ Outlook mỗi 60 giây khi trang Dashboard đang mở
    ui.timer(6000.0, sync_outlook_tasks)

    # Lấy dữ liệu từ database
    stats = get_dashboard_stats()
    overdue_tasks = get_overdue_tasks_list()
    inprogress_tasks = get_inprogress_tasks_list()
    pending_tasks = get_pending_tasks_list()
    chart_data = get_chart_data()

    # Màu nền của cả trang web (bên ngoài app)
    ui.query('body').style('background-color: #f0f2f5;')
    
    # Khung cửa sổ chính của App (Bo góc tròn, đổ bóng)
    with ui.row().classes('w-full max-w-[1280px] h-[850px] mx-auto mt-8 bg-[#f8fafc] rounded-[2rem] shadow-2xl overflow-hidden flex-nowrap border border-gray-200'):
        
        # --- 1. SIDEBAR BÊN TRÁI ---
        create_sidebar('home')

        # --- 2. NỘI DUNG CHÍNH BÊN PHẢI ---
        with ui.column().classes('flex-1 h-full p-10 overflow-y-auto bg-[#f8fafc] gap-0'):
            
            # Header (Lời chào + Icons góc phải)
            with ui.row().classes('w-full justify-between items-start mb-8'):
                with ui.column().classes('gap-1'):
                    ui.label('Good day, Chinh!').classes('text-[28px] font-extrabold text-gray-900 tracking-tight')
                    ui.label("Let's make today productive!").classes('text-sm text-gray-500 font-medium')
                
                with ui.row().classes('gap-5 items-center'):
                    ui.button('Sync Now', on_click=lambda: [ui.notify('Đang đồng bộ...'), sync_outlook_tasks()], icon='sync').props('flat dense color=blue').tooltip('Đồng bộ Outlook ngay')
                    ui.icon('search').classes('text-gray-400 cursor-pointer text-2xl hover:text-gray-600 transition-colors')
                    ui.icon('notifications').classes('text-gray-400 cursor-pointer text-2xl hover:text-gray-600 transition-colors')
                    ui.avatar('C').classes('bg-red-200 text-red-800 w-11 h-11 font-bold shadow-sm cursor-pointer')

            # Hàng Thống Kê (Stat Cards)
            with ui.row().classes('w-full gap-4 mb-8'):
                stat_card('done_all', 'text-blue-500', str(stats['completed']), 'Completed')
                stat_card('pending_actions', 'text-red-500', str(stats['pending']), 'Pending')
                stat_card('local_fire_department', 'text-orange-500', str(stats['overdue']), 'Overdue')
                stat_card('rocket_launch', 'text-purple-600', str(stats['active']), 'Active')
            
            # --- CHARTS ROW ---
            with ui.row().classes('w-full gap-6 mb-8'):
                # Biểu đồ tròn (Pie Chart)
                with ui.card().classes('flex-1 shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-4 border border-gray-100 bg-white').props('flat'):
                    ui.highchart({
                        'chart': {'type': 'pie', 'height': 300},
                        'title': {'text': 'Tasks by Category', 'align': 'left', 'style': {'fontSize': '16px', 'fontWeight': 'bold'}},
                        'plotOptions': {'pie': {'innerSize': '50%', 'dataLabels': {'enabled': False}, 'showInLegend': True}},
                        'series': [{'name': 'Tasks', 'data': chart_data['pie_data']}],
                        'credits': {'enabled': False}                   
                    }).classes('w-full')

                # Biểu đồ cột chồng (Column Chart)
                with ui.card().classes('flex-1 shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-4 border border-gray-100 bg-white').props('flat'):
                    ui.highchart({
                        'chart': {'type': 'column', 'height': 300},
                        'title': {'text': 'Completion Status', 'align': 'left', 'style': {'fontSize': '16px', 'fontWeight': 'bold'}},
                        'xAxis': {'categories': chart_data['column_data']['categories']},
                        'yAxis': {'title': {'text': 'Tasks'}},
                        'plotOptions': {'column': {'grouping': False, 'shadow': False, 'borderWidth': 0}},
                        'credits': {'enabled': False},
                        'series': [
                            {'name': 'Total Tasks', 'data': chart_data['column_data']['total'], 'color': 'rgba(165,170,217,1)', 'pointPadding': 0.3, 'pointPlacement': -0.2},
                            {'name': 'Completed', 'data': chart_data['column_data']['completed'], 'color': 'rgba(126,86,134,0.9)', 'pointPadding': 0.4, 'pointPlacement': -0.2}
                        ]
                    }).classes('w-full')
            # --- CARD: Overdue Tasks ---
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 mb-6 border border-gray-100 bg-white').props('flat'):
                # Header của Card
                with ui.row().classes('w-full justify-between items-center px-6 py-5 border-b border-gray-50'):
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-3'):
                            ui.label("Overdue Tasks").classes('text-xl font-extrabold text-gray-800')
                            ui.label(str(len(overdue_tasks))).classes('bg-red-100 text-red-600 px-2.5 py-0.5 rounded-full text-[11px] font-bold')
                        ui.label('Tasks that missed the deadline.').classes('text-[13px] text-gray-400 font-medium')
                    ui.icon('expand_less').classes('cursor-pointer text-gray-400 text-2xl hover:bg-gray-100 rounded-full p-1')

                # Danh sách công việc
                if not overdue_tasks:
                    ui.label('No overdue tasks! Great job.').classes('px-6 py-4 text-gray-500 italic')
                else:
                    for task in overdue_tasks:
                        project_name = task.project.name if task.project else "No Project"
                        date_str = task.due_date.strftime('%b %d') if task.due_date else "Unknown"
                        project_row(task.title, project_name, f'Due: {date_str}', due_color='text-red-600')

            # --- CARD: In Progress Tasks ---
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 mb-6 border border-gray-100 bg-white').props('flat'):
                with ui.row().classes('w-full justify-between items-center px-6 py-5 border-b border-gray-50'):
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-3'):
                            ui.label("In Progress").classes('text-xl font-extrabold text-gray-800')
                            ui.label(str(len(inprogress_tasks))).classes('bg-blue-100 text-blue-600 px-2.5 py-0.5 rounded-full text-[11px] font-bold')
                        ui.label('Tasks currently being worked on.').classes('text-[13px] text-gray-400 font-medium')
                    ui.icon('expand_less').classes('cursor-pointer text-gray-400 text-2xl hover:bg-gray-100 rounded-full p-1')

                if not inprogress_tasks:
                    ui.label('No tasks in progress.').classes('px-6 py-4 text-gray-500 italic')
                else:
                    for task in inprogress_tasks:
                        project_name = task.project.name if task.project else "No Project"
                        date_str = task.due_date.strftime('%b %d') if task.due_date else "No Date"
                        project_row(task.title, project_name, f'Due: {date_str}', due_color='text-blue-500')

            # --- CARD: Pending Tasks ---
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 mb-6 border border-gray-100 bg-white').props('flat'):
                with ui.row().classes('w-full justify-between items-center px-6 py-5 border-b border-gray-50'):
                    with ui.column().classes('gap-1'):
                        with ui.row().classes('items-center gap-3'):
                            ui.label("Pending Tasks").classes('text-xl font-extrabold text-gray-800')
                            ui.label(str(len(pending_tasks))).classes('bg-orange-100 text-orange-600 px-2.5 py-0.5 rounded-full text-[11px] font-bold')
                        ui.label('Tasks waiting to be started.').classes('text-[13px] text-gray-400 font-medium')
                    ui.icon('expand_less').classes('cursor-pointer text-gray-400 text-2xl hover:bg-gray-100 rounded-full p-1')

                if not pending_tasks:
                    ui.label('No pending tasks.').classes('px-6 py-4 text-gray-500 italic')
                else:
                    for task in pending_tasks:
                        project_name = task.project.name if task.project else "No Project"
                        date_str = task.due_date.strftime('%b %d') if task.due_date else "No Date"
                        project_row(task.title, project_name, f'Due: {date_str}', due_color='text-orange-500')
