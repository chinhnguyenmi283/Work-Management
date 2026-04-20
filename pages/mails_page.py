from datetime import datetime
from nicegui import ui
from sqlmodel import Session, select
from upload_data import engine, Task, delete_task
from components.sidebar import create_sidebar

@ui.page('/mails')
def mails_page():
    # --- LOGIC DATA ---
    def get_mail_data(search_term: str = None):
        with Session(engine) as session:
            statement = select(Task).where(Task.category == "Mail Responsed")
            
            if search_term:
                statement = statement.where(Task.title.contains(search_term))
            
            # Sắp xếp mới nhất lên đầu (dựa vào created_at)
            statement = statement.order_by(Task.id.desc())
            
            results = session.exec(statement).all()
            data = []
            for task in results:
                data.append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'date': task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else '-',
                    'outlook_id': task.outlook_id
                })
            return data

    # Hàm điều khiển bật Popup cửa sổ Mail gốc bên ứng dụng Outlook
    def open_in_outlook(outlook_id):
        if not outlook_id: return
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            mail = outlook.GetItemFromID(outlook_id)
            mail.Display() # Hiển thị popup email
        except Exception as e:
            ui.notify(f"Cannot open mail in Outlook: {e}", type='negative')
        finally:
            pythoncom.CoUninitialize()

    # --- UI SETUP ---
    ui.query('body').style('background-color: #f0f2f5;')

    # Khung chính
    with ui.row().classes('w-full max-w-[1280px] h-[850px] mx-auto mt-8 bg-[#f8fafc] rounded-[2rem] shadow-2xl overflow-hidden flex-nowrap border border-gray-200'):
        
        # --- 1. SIDEBAR ---
        create_sidebar('mails')

        # --- 2. NỘI DUNG CHÍNH ---
        with ui.column().classes('flex-1 h-full p-10 overflow-y-auto bg-[#f8fafc] gap-0'):
            
            # Header
            with ui.row().classes('w-full justify-between items-center mb-8'):
                with ui.column().classes('gap-1'):
                    ui.label('Mail Responsed').classes('text-[28px] font-extrabold text-gray-900 tracking-tight')
                    ui.label("List of emails synchronized from Outlook.").classes('text-sm text-gray-500 font-medium')
                
                with ui.row().classes('gap-4 items-center'):
                    search_field = ui.input(placeholder='Search emails...').props('outlined dense rounded').classes('w-64 bg-white')
                    with search_field.add_slot('prepend'):
                        ui.icon('search').classes('text-gray-400')

            # Bảng dữ liệu
            with ui.card().classes('w-full shadow-[0_4px_20px_rgba(0,0,0,0.03)] rounded-3xl p-0 border border-gray-100 bg-white overflow-hidden').props('flat'):
                
                columns = [
                    {'name': 'id', 'label': '#', 'field': 'id', 'sortable': True, 'align': 'left', 'classes': 'text-gray-400 font-bold w-16'},
                    {'name': 'title', 'label': 'Subject', 'field': 'title', 'sortable': True, 'align': 'left', 'classes': 'font-bold text-gray-800 ellipsis', 'style': 'max-width: 300px'},
                    {'name': 'description', 'label': 'Content Snapshot', 'field': 'description', 'align': 'left', 'classes': 'text-gray-500 ellipsis', 'style': 'max-width: 400px'},
                    {'name': 'date', 'label': 'Synced At', 'field': 'date', 'sortable': True, 'align': 'right', 'classes': 'text-gray-500'},
                    # {'name': 'action', 'label': 'Outlook', 'field': 'outlook_id', 'align': 'center'},
                ]
                
                # Thêm pagination=10 để phân mỗi trang 10 dòng
                table = ui.table(columns=columns, rows=get_mail_data(), row_key='id', pagination=10).classes('w-full no-shadow')
                
                def on_search():
                    table.rows = get_mail_data(search_field.value)
                    table.update()
                    
                search_field.on('input', on_search)
                
                # Xử lý khi click vào 1 dòng để xem chi tiết
                def show_mail_details(e):
                    row_data = e.args[1]
                    with ui.dialog() as dialog, ui.card().classes('w-[600px] p-6'):
                        ui.label(row_data['title']).classes('text-xl font-bold mb-2')
                        ui.label(f"Synced At: {row_data['date']}").classes('text-xs text-gray-500 mb-4')
                        ui.separator()
                        ui.label(row_data['description']).classes('text-sm text-gray-800 mt-4 whitespace-pre-wrap')
                        
                        with ui.row().classes('w-full justify-between mt-6'):
                            def delete_and_close():
                                delete_task(row_data['id'])
                                dialog.close()
                                on_search() # Refresh lại bảng
                            ui.button('Delete', on_click=delete_and_close).props('flat color=red')
                            with ui.row().classes('gap-2'):
                                ui.button('Open in Outlook', on_click=lambda: open_in_outlook(row_data.get('outlook_id'))).props('color=blue flat')
                                ui.button('Close', on_click=dialog.close).props('flat color=black')
                    dialog.open()
                
                table.on('rowClick', show_mail_details)
                table.props('flat bordered=false square')
                
                # Cột Action mở email trực tiếp bên bảng Grid
                table.on('open_outlook', lambda e: open_in_outlook(e.args['outlook_id']))
                table.add_slot('body-cell-action', '''
                    <q-td :props="props">
                        <q-btn flat round dense icon="open_in_new" color="blue" @click.stop="$emit('open_outlook', props.row)">
                            <q-tooltip>Mở thư này trên Outlook</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')