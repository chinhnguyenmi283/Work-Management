from nicegui import ui



def stat_card(icon_name, icon_color_class, count, label):
    """Vẽ thẻ thống kê (Completed, Pending, Overdue, Active)."""
    with ui.card().classes('flex flex-row items-center gap-3 shadow-[0_4px_12px_rgba(0,0,0,0.03)] rounded-2xl px-5 py-3.5 flex-1 bg-white border border-gray-100').props('flat'):
        ui.icon(icon_name).classes(f'text-2xl {icon_color_class}')
        with ui.row().classes('items-baseline gap-1'):
            ui.label(count).classes('font-extrabold text-xl text-gray-800')
            ui.label(label).classes('text-sm text-gray-500 font-medium')

def project_row(title, subtitle, due_text, due_color='text-red-500', checked=False):
    """Vẽ một hàng hiển thị thông tin dự án."""
    with ui.row().classes('w-full items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0 flex-nowrap'):
        # Cột bên trái: Checkbox + Icon + Tiêu đề
        with ui.row().classes('items-center gap-4 flex-1 min-w-0'):
            ui.checkbox(value=checked).props('color=grey-4')
            # Dùng icon mặc định thay cho ảnh 3D trong mẫu
            ui.icon('space_dashboard', color='primary').classes('text-3xl opacity-80')
            with ui.column().classes('gap-0.5'):
                ui.label(title).classes('font-bold text-[15px] text-gray-800 tracking-tight')
                ui.label(subtitle).classes('text-xs text-gray-400 font-medium')
        
        # Cột bên phải: Ngày tháng + Avatars + Nút 3 chấm
        with ui.row().classes('items-center gap-6 shrink-0'):
            # Ngày tháng
            with ui.row().classes('items-center gap-1.5'):
                ui.icon('calendar_month').classes(f'text-[16px] {due_color}')
                ui.label(due_text).classes('text-xs text-gray-500 font-medium')
            
            # Avatars (Chồng lên nhau bằng class -space-x-2 của Tailwind)
            with ui.row().classes('items-center -space-x-2'):
                ui.avatar('👤').classes('w-8 h-8 text-sm bg-pink-100 text-pink-600 border-2 border-white shadow-sm')
                ui.avatar('🧔').classes('w-8 h-8 text-sm bg-blue-100 text-blue-600 border-2 border-white shadow-sm')
            
            # Nút menu 3 chấm
            ui.button(icon='more_vert').props('flat round dense text-color=grey-5').classes('w-8 h-8 hover:bg-gray-200')

