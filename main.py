# Import necessary modules and libraries
from customtkinter import (
    CTk,
    CTkFrame,
    CTkButton,
    CTkCheckBox,
    CTkEntry,
    CTkScrollableFrame,
    CTkImage,
    CTkToplevel,
    CTkLabel,
)
from tkinter import END, IntVar
from PIL import Image
import pymysql

# Database connection credentials
sqlCred = {
    "host": "localhost",
    "user": "python",
    "password": "python",
    "database": None,
    "port": 9999,
}

# Class for managing tasks
class TaskManager:
    def __init__(self, masterFrame: CTkScrollableFrame):
        # Dictionary to store task information
        self.taskList = dict()
        self.master = masterFrame
        self.hideCompleted = False

    def addTask(self, taskString: str, taskStatus: int = 0, initialize: bool = False):
        # Create a task item based on the length of the task string
        if not len(taskString.strip()):
            return
        deleteButton.configure(state="normal")
        taskInput.delete(0, END)
        if len(taskString) > 26:
            taskItem = CTkScrollableFrame(
                master=self.master, orientation="horizontal", height=40
            )
        else:
            taskItem = CTkFrame(master=self.master)

        # Create a checkbox for the task
        taskCheck = CTkCheckBox(
            master=taskItem,
            text=taskString,
            font=("monospace", 15),
        )
        # Store task information in the taskList dictionary
        self.taskList[taskCheck.__hash__()] = [taskItem, taskCheck, taskString]

        # Set up the checkbox variable and configure its command
        checkbox_var = IntVar()
        checkbox_var.set(taskStatus)
        taskCheck.configure(
            command=lambda: self.update(self.taskList[taskCheck.__hash__()]),
            variable=checkbox_var,
        )

        # Configure the checkbox appearance and pack the task item
        taskCheck.anchor("w")
        taskCheck.grid(padx=10, pady=10)
        taskItem.pack(padx=10, pady=10, fill="x")

        # Insert the task into the database if not initializing
        if not initialize:
            cursor.execute("INSERT INTO taskTable VALUES (%s, 0);", (taskString))
            displayDB()

    def update(self, taskItem):
        # Update the task status in the database and display it
        cursor.execute(
            "UPDATE taskTable SET status=%s WHERE taskString=%s;",
            (taskItem[1].get(), taskItem[2]),
        )
        displayDB()
        # Hide or show the task based on completion status and hideCompleted flag
        if self.hideCompleted and taskItem[1].get():
            taskItem[0].forget()
            if isinstance(taskItem[0], CTkScrollableFrame):
                taskItem[0]._parent_frame.forget()
        elif not self.hideCompleted:
            taskItem[0].pack(padx=10, pady=10, fill="x")

    def showOrHideCompleted(self, status: bool):
        # Set the hideCompleted flag and update tasks accordingly
        self.hideCompleted = status
        for item in self.taskList.values():
            self.update(item)


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

def displayDB():
    # Display tasks from the database
    cursor.execute("SELECT * FROM taskTable;")
    tableRows = cursor.fetchall()
    print("=" * 50)
    for row in tableRows:
        print(row[0], ":", row[1])

def proceedDeleting(option: str, warning: CTkToplevel):
    if option == "delete":
        deleteButton.configure(state="disabled")
        cursor.execute("DELETE FROM taskTable;")
        for taskItem in taskManager.taskList.values():
            taskItem[0].destroy()
            if isinstance(taskItem[0], CTkScrollableFrame):
                taskItem[0]._parent_frame.destroy()
        del taskManager.taskList
        taskManager.taskList = dict()
    warning.destroy()
    app.update()

def deleteData():
    deleteWarning = CTkToplevel()
    deleteWarning.resizable(False, False)
    deleteWarning.grab_set()
    warningLabel = CTkLabel(master=deleteWarning, text="⚠️This will erase all data⚠️")
    warningLabel.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    proceedButton = CTkButton(
        master=deleteWarning,
        text="Proceed",
        command=lambda: proceedDeleting("delete", deleteWarning),
    )
    proceedButton.grid(row=1, column=0, padx=10, pady=10)
    cancelButton = CTkButton(
        master=deleteWarning,
        text="Cancel",
        command=lambda: proceedDeleting("cancel", deleteWarning),
    )
    cancelButton.grid(row=1, column=1, padx=10, pady=10)

def close_connection():
    # Close the database connection and exit the application
    cursor.close()
    connection.commit()
    connection.close()
    app.destroy()

# UI Definition
app = CTk()
app.title("Personal Task Manager")
app.geometry("370x550")
app.minsize(370, 550)
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

# Scrollable frame for displaying the list of tasks
taskListFrame = CTkScrollableFrame(master=mainFrame)
taskListFrame.pack(padx=10, pady=10, expand=True, fill="both")

# Initialize the task manager
taskManager = TaskManager(taskListFrame)

# Button to add a task
addTaskButton = CTkButton(
    master=taskManagerFrame,
    text="ADD",
    width=60,
    command=lambda: taskManager.addTask(taskInput.get()),
)
addTaskButton.grid(row=0, column=1, padx=10, pady=10)

# Button to toggle between hiding and showing tasks
hideCompletedCheck = CTkCheckBox(
    master=taskManagerFrame, text="Hide Completed", font=("monospace", 15)
)
hideCompletedCheck.configure(
    command=lambda: taskManager.showOrHideCompleted(hideCompletedCheck.get())
)
hideCompletedCheck.grid(row=1, column=0, padx=10, pady=10)

deleteButton = CTkButton(
    master=taskManagerFrame,
    text=None,
    width=60,
    image=CTkImage(Image.open("./images/bin.png")),
    command=deleteData,
)
deleteButton.grid(row=1, column=1, padx=10, pady=10)

# Populate the task manager with tasks from the database
cursor.execute("SELECT * FROM taskTable;")
for row in cursor.fetchall():
    taskManager.addTask(row[0], row[1], True)

# Application close protocol
app.protocol("WM_DELETE_WINDOW", close_connection)

# Start the main event loop
app.mainloop()
