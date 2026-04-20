import pythoncom
import win32com.client
from sqlmodel import Session, select
from upload_data import engine, Task, create_task
from datetime import datetime

def sync_outlook_tasks():
    """
    Kết nối với Outlook, tìm các email có Category='Lending'.
    Nếu email chưa có trong database, tạo Task mới với Category='Mail Responsed'.
    """
    print("🔄 Bắt đầu tiến trình đồng bộ Outlook...")
    try:
        # Cần thiết khi chạy trong thread/timer của NiceGUI
        pythoncom.CoInitialize()
        
        # Kết nối tới Outlook
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        
        # Lấy danh sách các Outlook ID đã tồn tại trong DB để tránh trùng
        with Session(engine) as session:
            existing_ids = session.exec(select(Task.outlook_id).where(Task.outlook_id != None)).all()
            existing_ids_set = set(existing_ids)

        new_tasks_count = 0
        
        # Duyệt qua tất cả các tài khoản (Stores) đã đăng nhập trong Outlook
        for store in outlook.Stores:
            try:
                print(f"📧 Đang quét tài khoản: {store.DisplayName}")
                inbox = store.GetDefaultFolder(6) # 6 là Inbox
                
                items = inbox.Items
                items.Sort("[ReceivedTime]", True)
                
                checked_count = 0
                item = items.GetFirst()
                
                # Duyệt qua 50 email gần nhất của tài khoản này
                while item and checked_count < 50:
                    try:
                        checked_count += 1
                        
                        # Kiểm tra xem item có Categories không
                        if hasattr(item, 'Categories') and item.Categories:
                            if 'lending' in item.Categories.lower():
                                mail_id = item.EntryID
                                
                                if mail_id not in existing_ids_set:
                                    subject = item.Subject
                                    try:
                                        body = item.Body[:500] + "..." if len(item.Body) > 500 else item.Body
                                    except:
                                        body = ""
                                    
                                    create_task(
                                        title=subject,
                                        description=f"Imported from Outlook ({store.DisplayName}): {body}",
                                        category="Mail Responsed",
                                        priority=2,
                                        status="Completed",
                                        outlook_id=mail_id,
                                        due_date=datetime.now()
                                    )
                                    new_tasks_count += 1
                                    print(f"Đã import task từ mail: {subject}")
                    except:
                        pass
                    
                    item = items.GetNext()
            except Exception as e:
                print(f"⚠️ Không thể truy cập Inbox của {store.DisplayName}: {e}")

        if new_tasks_count > 0:
            from nicegui import ui
            ui.notify(f'Đã đồng bộ {new_tasks_count} task mới từ Outlook!', type='positive')

    except Exception as e:
        print(f"Không thể kết nối Outlook: {e}")
    finally:
        # Giải phóng tài nguyên COM
        pythoncom.CoUninitialize()
