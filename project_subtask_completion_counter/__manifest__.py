{
    "name": "Project Sub-task Completion Counter",
    "version": "19.0.1.5.0",
    "summary": "Subtask progress counter, draggable manual order and automatic done-at-bottom reordering",
    "category": "Project",
    "author": "Cátia Silva Advicebiz",
    "license": "LGPL-3",
    "depends": ["project", "web"],
    "data": [
        "views/project_task_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_subtask_completion_counter/static/src/css/subtask_progress.css",
        ],
    },
    "installable": True,
    "application": False,
}
