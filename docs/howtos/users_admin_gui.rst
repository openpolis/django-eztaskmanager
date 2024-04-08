.. _django-admin-section:

Managing Tasks in Django Admin Site
---------------------------------------

This guide is intended for **users** who want to manage tasks using Django's built-in administrative interface.

It is assumed that these users are familiar with the basic functionality of a Django admin interface,
therefore CRUD (Create, Read, Update, Delete) operations won't be covered here.

Upon successful login to the admin site of your application, a **Task Manager** section will be visible,
providing you the ability to manage your tasks.

Within the Django admin site, the **Task Manager** section will include the application's
views.

.. image:: /_static/images/admin_gui_1.png
  :width: 800
  :alt: The task manager section appears


Gathering commands
^^^^^^^^^^^^^^^^^^

Commands for tasks should be gleaned from the host project's applications, specifically among
those tasks that have been defined for management. This will enable them to be available as *launchable* commands.

This process can be achieved using the ``collectcommands`` management task [#excludecore]_.

.. code-block:: bash

    python manage.py collect_commands --excludecore -v2


.. image:: /_static/images/admin_gui_2.png
  :width: 800
  :alt: The list of commands

Complete syntax of a command can be found on the command details page, which is accessible by clicking on the
application name in the command's row.

.. image:: /_static/images/admin_gui_3.png
  :width: 800
  :alt: A command's syntax


Commands are removable. To recreate tasks from these deleted commands,
re-running the ``collectcommands`` task will be necessary.

Only those commands flagged as ``active`` can be utilised to generate tasks.
Hence, to prevent a command from being used to create tasks, simply turn its ``active`` status to false.

.. note::

You can also generate a task using the ``collectcommands`` command.
This allows you to launch the collection of available commands directly through django-eztaskmanager.

Tasks Overview
^^^^^^^^^^^^^^
The `Tasks` section serves as the central administration view where every operation takes place. Tasks can be listed, filtered, searched, created, modified, and removed using Django-admin's standard CRUD processes.

.. image:: /_static/images/admin_gui_4.png
  :width: 800
  :alt: Django tasks list view with custom bulk actions

You have the capabilities to start or stop a task both in the *list view* and the *detail view*.

.. image:: /_static/images/admin_gui_5.png
  :width: 800
  :alt: Django task details view with custom buttons

By default, tasks are sorted according to their latest launch time. This ensures that the most frequently used tasks are displayed upfront, avoiding clutter by infrequently used tasks. Additional sorting criteria can be applied by clicking the column headers.

The outcomes of the tasks are indicated both color-coded and with detailed notes of errors/warnings, if any. Tasks with warnings or errors (yellow and orange color codes) might still be functioning as expected as sometimes the errors can be attributed to issues with the data source. Tasks that fail (red code) require immediate attention as it suggests there are issues within the task's code or logic itself.

Clicking on the last result status opens a new tab providing log messages for that particular task execution.

Hovering over the task name reveals a descriptive note, given that the task authors have added one. This note can provide insight into different aspects of the task instance and highlight any peculiarities of the arguments needed.

Task Structure
^^^^^^^^^^^^^^
A task is comprised of four main sections:

- **Definition**: Contains the task name, command, arguments, category, and notes.
- **Scheduling**: Specifies the start time and recurrence rate.
- **Last Execution**: Shows the queued job id, status, last execution datetime, last result, next execution, and the count of warnings or errors.
- **Reports**: Every execution of a task generates a **Report**. Only the last five reports are stored and shown in each task's detail view.

Task Definition
^^^^^^^^^^^^^^^

.. image:: /_static/images/admin_gui_6.png
  :width: 800
  :alt: Django definition fields

The **Definition** section contains the following fields:

- **Name**: This is where you provide a unique name for the task. Using unique names with prefixes can facilitate easy visual identification of tasks.

  .. note::

    Remember that one command can be applied to multiple tasks with different arguments. Ensure that you give distinct **names** and describe the differences in detail in the **note** field. This will help other users make informed decisions about which task to use.

- **Command**: Select the appropriate command from the list available in the command popup.
- **Arguments**: Here, you enter the arguments the command requires using a specific syntax:

  .. note::

      Single arguments should be separated by a *comma* (","), while multiple values within a single argument should be separated by a space.

      For example: ``-f, --secondarg param1 param2, --thirdarg=pippo, --thirdarg``

- **Category**: Choose an existing category or create a new one for the task.
- **Note**: This field is for a descriptive note explaining how the command or its arguments are used.

Task Categories
^^^^^^^^^^^^^^^

Task categories are an efficient way of managing tasks when their quantity starts to increase. You can assign a category to each task and then filter the tasks list by category.

.. note::

    Keep your category names simple and short. Try to limit the total number of categories to less than ten to avoid any confusion for other users.

Task Scheduling
^^^^^^^^^^^^^^^

.. image:: /_static/images/admin_gui_7.png
  :width: 800
  :alt: Django scheduling fields

The **Scheduling** process involves the following fields:

- **Scheduling**: Specify a date and time for the task's initial launch.
- **Repetition Period**: Select a frequency for the task to repeat: *minute*, *hour*, *day*, or *month*.
- **Repetition Rate**: Set a numerical value for the task's repetition rate.

- To **schedule a one-time future task**: Set the scheduling field to a future time and press the start button.
- To **schedule a recurring future task**: Set both scheduling and repetition fields, then press the start button.
- To **cancel a scheduled start**: Press the stop button.


Understanding the Task's Last Execution Status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: /_static/images/admin_gui_8.png
  :width: 800
  :alt: Django task's last execution status

The fields in this section are *read-only* and display information about the task's last execution.

- **Status**: This can show one of the following:
  - ``IDLE``: The task has either never started or it was stopped.
  - ``STARTED``: The task is currently running.
  - ``SCHEDULED``: The task is set to start at some point in the future.

- **Last Datetime**: This shows the date and time of the last execution.
- **Last Result**: This shows the result of the last execution:

  - ``OK``: The task ran without any errors or warnings.
  - ``WARNINGS``: The task ran correctly, but with warnings. Refer to the report for details.
  - ``ERRORS``: The task ran correctly, but with errors. Refer to the report for details.
  - ``FAILED``: There was a runtime error. Refer to the report for details.

- **Errors**: This shows the number of detected errors from the last execution.
- **Warnings**: This shows the number of detected warnings from the last execution.

.. note::

    Before a task starts for the first time, it is put in the spooler. Therefore, the task's status may show as ``SPOOLED``. A few moments later, after refreshing the page, the status will change to ``STARTED``. This is to be expected.

Reading the Task's Reports
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: /_static/images/admin_gui_9.png
  :width: 800
  :alt: Django tasks reports

After a task is complete, a report is generated and added to the **reports** section. To conserve space, only the last 5 reports remain accessible for users.

Each report includes the **result** and **invocation datetime** fields, plus the last 10 log lines from the execution.

Clicking on the *show the log messages* link opens a new page containing the log messages.

.. image:: /_static/images/admin_gui_10.png
  :width: 800
  :alt: Django tasks report with log messages

If the task is still running, the page will refresh to display new messages as they're added.

At the top of the page is a **toolbar** divided into three sections:

 - **Levels Buttons** (``ALL``, ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``): These function as filters. Clicking one only shows messages of that type. The numbers next to each button indicate the amount of messages per type. A button only appears after a message of its type has been added to the log file.
 - **Search Field**: This helps in filtering messages by a specific string. Only messages containing this string are listed. Clicking on the 'x' button next to the search field will reset all filters (equivalent to pressing the ``ALL`` button).
 - Commands on the right side of the toolbar:
   - The **raw logs** button opens a new page displaying the log files in raw text format.
   - The **sticky mode** button toggles the auto-scrolling of message displays. This can be used to focus on a specific part of the log messages.

.. note::

    The entire list of log messages is rendered on a single page. This can cause long rendering times for lengthy lists. The recommended solution is to implement tasks that do not log excess messages... rubric:: Footnotes

.. [#excludecore] The `excludecore` parameter is used to prevent the fetching of core Django tasks.