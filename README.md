A personal web application to manage tasks, track progress, and synchronize tasks from Outlook. This project is built entirely in Python using the NiceGUI library for the user interface.

<img width="1875" height="948" alt="{7D42F745-6BFB-4E6C-8976-B368BB24D1FE}" src="https://github.com/user-attachments/assets/d9780f2a-14b2-439f-a2f9-9e71a909d5e6" />


# 🌟 Key Features
## Dashboard: Provides a comprehensive overview of key metrics:
- Number of tasks completed today.
- Number of pending tasks.
- Number of overdue tasks.
- Charts for analyzing tasks by category and progress.
## My Tasks:
- Easily create, view, edit, and delete tasks through an intuitive popup interface.
- Categorize tasks by project, priority, and status (Pending, In Progress, Completed).
- Add sub-tasks and track their completion progress directly within the task details.
- Attach relevant links to tasks.
## Outlook Sync (Mails):
- Automatically scans and syncs emails from Outlook with the Lending category into the application as completed tasks.
- View a list of synchronized emails with a summary of their content.
- Open the original email directly in the Outlook application from the web interface for detailed viewing.
## History:
- Archive and review all completed tasks.
- Supports searching and filtering within the archive.
- Modern UI: A clean design inspired by professional task management applications, built with NiceGUI components and TailwindCSS.
# 🛠️ Tech Stack
- Backend & Frontend: NiceGUI (based on FastAPI and Vue/Quasar)
- Database: SQLModel and SQLite
- Outlook Interaction: pywin32
- Language: Python 3