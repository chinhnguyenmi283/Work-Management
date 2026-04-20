from nicegui import ui

def nav_item(icon_name, text, active=False, on_click=None):
    """Vẽ một mục trong thanh menu bên trái."""
    # Đổi màu nền và font chữ nếu mục đó đang được chọn (active)
    bg_class = 'bg-white shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold text-gray-900' if active else 'hover:bg-gray-100 text-gray-600 font-medium'
    
    with ui.row().classes(f'w-full items-center gap-3 px-4 py-2.5 rounded-xl cursor-pointer transition-colors {bg_class}').on('click', on_click):
        # Quasar sử dụng Material Icons
        ui.icon(icon_name).classes('text-xl text-gray-400' if not active else 'text-xl text-orange-400')
        ui.label(text).classes('text-sm')
