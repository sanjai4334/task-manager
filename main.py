# Importing necessary modules and libraries
from customtkinter import (
    CTk,
    CTkFrame,
    CTkButton,
    CTkCheckBox,
    CTkEntry,
    CTkScrollableFrame,
    CTkImage,
)
from PIL import Image
from tkinter import END
import pymysql


# Database connection credentials
sqlCred = {
    "host": "localhost",
    "user": "username",
    "password": "password",
    "database": None,
    "port": 3306,
}


# Class for managing a stack of completed tasks
class TaskStack:
    def __init__(self):
        self.stack = []

    def push(self, taskString, isInitializing=False):
        # Marks a task as completed in the database
        if not isInitializing:
            cursor.execute(
                "UPDATE taskTable SET status=1 WHERE taskString=%s", (taskString)
            )
        undoButton.configure(state="normal")
        self.stack.append(taskString)

    def pop(self) -> str:
        # Marks the most recently completed task as incomplete in the database
        taskString = self.stack.pop()
        if not self.stack:
            undoButton.configure(state="disabled")

        cursor.execute(
            "UPDATE taskTable SET status=0 WHERE taskString=%s", (taskString)
        )
        return taskString

# Instance of TaskStack for completed tasks
completedTasks = TaskStack()

# Class for managing the list of tasks displayed in the UI
class TaskList:
    def __init__(self, master: CTkFrame):
        self.master = master
        self.taskItems = dict()

    def append(self, taskInfo: str):
        # Adds a new task to the list
        if len(taskInfo) > 37:
            taskItem = CTkScrollableFrame(
                master=self.master, orientation="horizontal", height=40
            )
        else:
            taskItem = CTkFrame(master=self.master)

        taskCheck = CTkCheckBox(master=taskItem, text=taskInfo, font=("monospace", 15))
        taskCheck.configure(command=lambda: self.remove(taskCheck.__hash__()))
        taskCheck.anchor("w")
        taskCheck.grid(padx=10, pady=10)

        self.taskItems[taskCheck.__hash__()] = [taskItem, taskInfo]
        self.load()

    def remove(self, taskItemHash):
        # Removes a task and stores it in the completed task stack
        taskItem = self.taskItems.pop(taskItemHash)
        taskItem[0].destroy()

        if isinstance(taskItem[0], CTkScrollableFrame):
            taskItem[0]._parent_frame.destroy()

        completedTasks.push(taskItem[1])
        cursor.execute("SELECT * FROM taskTable;")
        print(cursor.fetchall())

    def load(self):
        # Displays all the current tasks
        taskItem: CTkFrame
        for taskItem in self.taskItems.values():
            taskItem[0].pack(padx=10, pady=10, fill="x")  # type: ignore
        cursor.execute("SELECT * FROM taskTable;")
        print(cursor.fetchall())

# Function to add a task
def addTask():
    taskString = taskInput.get()
    if taskString:
        # Inserts a new task into the database and adds it to the task list
        cursor.execute("INSERT INTO taskTable VALUES (%s, 0);", (taskString))
        taskList.append(taskString)
        taskInput.delete(0, END)

# Function to toggle between showing completed and incomplete tasks
def showCompletedTasks():
    if showCompletedButton.cget("text") == "Show Completed":
        showCompletedButton.configure(text="Show Incomplete")

        for widget in taskManagerFrame.children.values():
            widget.configure(state="disabled")  # type: ignore

    else:
        showCompletedButton.configure(text="Show Completed")

        for widget in taskManagerFrame.children.values():
            widget.configure(state="normal")  # type: ignore

# Database Initialization
with pymysql.connect(
    host=sqlCred["host"],
    user=sqlCred["user"],
    password=sqlCred["password"],
    port=sqlCred["port"],
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS taskManager;")
        sqlCred["database"] = "taskManager"

# Connecting to the database
connection = pymysql.connect(
    host=sqlCred["host"],
    user=sqlCred["user"],
    password=sqlCred["password"],
    database=sqlCred["database"],
    port=sqlCred["port"],
)

cursor = connection.cursor()

# Creating the taskTable if it doesn't exist
cursor.execute("CREATE TABLE IF NOT EXISTS taskTable(taskString TEXT, status INTEGER);")

# Function to close the database connection and exit the application
def close_connection():
    cursor.close()
    connection.commit()
    connection.close()
    app.destroy()

# UI Definition
app = CTk()
app.title("Personal Task Manager")
app.geometry("450x550")
app.minsize(450, 550)
app.resizable(False, True)
app.iconbitmap("./images/taskManagerIcon.ico")

# Main container frame
mainFrame = CTkFrame(master=app)
mainFrame.pack(padx=10, pady=10, expand=True, fill="both")

# Frame for task input, add task button, and undo button
taskManagerFrame = CTkFrame(master=mainFrame)
taskManagerFrame.pack(padx=10, pady=10, fill="x")

# Entry widget for task input
taskInput = CTkEntry(master=taskManagerFrame, width=225)
taskInput.grid(row=0, column=0, padx=10, pady=10)

# Button to add a task
addTaskButton = CTkButton(
    master=taskManagerFrame, text="ADD", width=60, command=addTask
)
addTaskButton.grid(row=0, column=1, padx=10, pady=10)

# Undo button with undo icon
undoIcon = Image.open("./images/undo.png")
undoButton = CTkButton(
    master=taskManagerFrame,
    text=None,  # type: ignore
    image=CTkImage(undoIcon),
    width=60,
    command=lambda: taskList.append(completedTasks.pop()),
    state="disabled",
)
undoButton.grid(row=0, column=2, padx=10, pady=10)

# Scrollable frame for displaying the list of tasks
taskListFrame = CTkScrollableFrame(master=mainFrame)
taskListFrame.pack(padx=10, pady=10, expand=True, fill="both")

# Button to toggle between showing completed and incomplete tasks
showCompletedButton = CTkButton(
    master=mainFrame, text="Show Completed", command=showCompletedTasks
)

taskList = TaskList(taskListFrame)  # type: ignore

# Add tasks to taskStack and taskList
cursor.execute("SELECT taskString FROM taskTable WHERE status=0")
incompleteTaskList = cursor.fetchall()
if incompleteTaskList:
    for taskString in incompleteTaskList:
        taskList.append(taskString[0])

cursor.execute("SELECT taskString FROM taskTable WHERE status=1")
completedTaskList = cursor.fetchall()
if completedTaskList:
    for taskString in completedTaskList:
        completedTasks.push(taskString[0], True)

# Application close protocol
app.protocol("WM_DELETE_WINDOW", close_connection)

# Start the main event loop
app.mainloop()
