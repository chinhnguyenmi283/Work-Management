import os
from nicegui import ui
from upload_data import create_db_and_tables, sqlite_file_name, engine, migrate_outlook_tasks

# Import các trang
from pages import dashboard, tasks_page, history_page, mails_page
# import theme

# Khởi tạo database khi chạy app
# --- RESET DATABASE (Xóa file cũ để tạo lại từ đầu) ---
# if os.path.exists(sqlite_file_name):
#     try:
#         engine.dispose() # Đóng mọi kết nối đến database trước khi xóa
#         os.remove(sqlite_file_name)
#         print("Đã xóa database cũ để reset dữ liệu.")
#     except PermissionError:
#         print("⚠️ CẢNH BÁO: Không thể xóa 'database.db' vì đang được sử dụng. Hãy đóng DB Browser hoặc tắt các terminal python cũ.")

# create_db_and_tables()
create_db_and_tables()
migrate_outlook_tasks()

ui.run(title='Work Management', port=8080, favicon='🚀')