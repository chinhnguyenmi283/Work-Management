from nicegui import ui

def menu():
    """Tạo menu bên trái cho ứng dụng"""
    with ui.left_drawer(value=True).classes('bg-slate-100') as drawer:
        ui.label('WORK MANAGER').classes('text-h6 q-pa-md font-bold text-primary')
        
        with ui.column().classes('w-full gap-0'):
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/'), icon='dashboard').props('flat align=left').classes('w-full')
            ui.button('Tasks', on_click=lambda: ui.navigate.to('/tasks'), icon='list').props('flat align=left').classes('w-full')
            ui.button('HR & Payroll', on_click=lambda: ui.navigate.to('/hr'), icon='people').props('flat align=left').classes('w-full')
            ui.separator().classes('my-2')
            ui.button('Settings', icon='settings').props('flat align=left').classes('w-full')

def frame(page_title: str):
    """Decorator để áp dụng layout chung cho các trang"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Header
            with ui.header().classes('bg-primary text-white shadow-2'):
                ui.button(on_click=lambda: ui.left_drawer.toggle(), icon='menu').props('flat round dense')
                ui.label(page_title).classes('text-lg font-bold ml-4')
            
            # Menu bên trái
            menu()
            
            # Nội dung chính của trang
            with ui.column().classes('w-full p-4'):
                func(*args, **kwargs)
        return wrapper
    return decorator