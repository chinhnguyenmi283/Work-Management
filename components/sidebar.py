from nicegui import ui
from components.navigation import nav_item

def create_sidebar(active_page: str):
    """Tạo thanh sidebar dùng chung cho tất cả các trang."""
    with ui.column().classes('w-[260px] h-full p-6 border-r border-gray-200 justify-between bg-[#f8fafc] shrink-0'):
        with ui.column().classes('w-full gap-8'):
            # Logo
            with ui.row().classes('items-center gap-2 px-2'):
                ui.icon('check_circle').classes('text-2xl text-yellow-500')
                ui.label('Taskly').classes('font-extrabold text-xl tracking-tight text-gray-800')
            
            # Menu
            with ui.column().classes('w-full gap-1'):
                ui.label('MAIN MENU').classes('text-[11px] text-gray-400 font-bold mb-1 px-2 tracking-wider')
                nav_item('home', 'Home', active=(active_page == 'home'), on_click=lambda: ui.navigate.to('/'))
                nav_item('task', 'My Tasks', active=(active_page == 'tasks'), on_click=lambda: ui.navigate.to('/tasks'))
                nav_item('mail', 'Mails', active=(active_page == 'mails'), on_click=lambda: ui.navigate.to('/mails'))
                nav_item('history', 'History', active=(active_page == 'history'), on_click=lambda: ui.navigate.to('/history'))
                # nav_item('folder_copy', 'Projects', active=(active_page == 'projects'))
                # nav_item('calendar_today', 'Calendar', active=(active_page == 'calendar'))
            
            # Other
            with ui.column().classes('w-full gap-1'):
                ui.label('OTHER').classes('text-[11px] text-gray-400 font-bold mb-1 px-2 tracking-wider mt-2')
                nav_item('help_outline', 'Help Center')
                nav_item('settings', 'Settings', active=(active_page == 'settings'))
        
        # Logout
        with ui.row().classes('w-full items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-200 rounded-xl transition-colors mt-auto'):
            ui.icon('logout').classes('text-gray-500 text-xl')
            ui.label('Logout').classes('text-sm text-gray-700 font-bold')