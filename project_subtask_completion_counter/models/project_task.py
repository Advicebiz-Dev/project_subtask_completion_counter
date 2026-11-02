from odoo import api, fields, models


# The Sub-tasks x2many list must be ordered by `sequence` first.  The web
# client's handle widget will otherwise disable drag-and-drop.
_REORDER_CONTEXT_KEY = "subtask_completion_skip_auto_resequence"
_DONE_STATE = "1_done"
_SEQUENCE_STEP = 10


class ProjectTask(models.Model):
    _inherit = "project.task"

    completed_subtask_count = fields.Integer(
        string="Completed Sub-tasks",
        compute="_compute_subtask_progress",
        export_string_translation=False,
    )

    completed_subtask_percentage = fields.Integer(
        string="Completed Percentage",
        compute="_compute_subtask_progress",
        export_string_translation=False,
    )

    completed_subtask_display = fields.Char(
        string="Sub-task Progress",
        compute="_compute_subtask_progress",
        export_string_translation=False,
    )

    # Retained for compatibility with the module's previous release.
    # It is deliberately NOT the first sorting key in the list any more.
    is_subtask_completed = fields.Boolean(
        string="Sub-task Completed",
        compute="_compute_is_subtask_completed",
        store=True,
        index=True,
        export_string_translation=False,
    )

    @api.depends("child_ids.state")
    def _compute_subtask_progress(self):
        for task in self:
            total = len(task.child_ids)
            completed = len(
                task.child_ids.filtered(lambda subtask: subtask.state == _DONE_STATE)
            )
            percentage = round((completed / total) * 100) if total else 0
            task.completed_subtask_count = completed
            task.completed_subtask_percentage = percentage
            task.completed_subtask_display = (
                f"{completed}/{total} Concluídas {percentage}%"
            )

    @api.depends("state")
    def _compute_is_subtask_completed(self):
        for task in self:
            task.is_subtask_completed = task.state == _DONE_STATE

    @api.model
    def _normalize_subtask_order(self, parent_ids, append_ids=()):
        """Preserve manual sibling order, grouping completed tasks at the end.

        Only called when a subtask is created, changes parent, or changes its
        completed/not-completed status. In particular, a manual write of
        `sequence` never triggers this method: the user's drag-and-drop is
        persisted by the native Odoo x2many mechanism.

        `append_ids` marks newly inserted/moved tasks. Within their respective
        completed/open groups they are put after existing tasks.
        """
        if not parent_ids:
            return

        append_ids = set(append_ids)
        task_model = self.sudo().with_context(active_test=False)
        siblings = task_model.search(
            [("parent_id", "in", list(parent_ids))],
            order="parent_id asc, sequence asc, id asc",
        )
        by_parent = {}
        for sibling in siblings:
            by_parent.setdefault(sibling.parent_id.id, []).append(sibling)

        for parent_siblings in by_parent.values():
            desired = sorted(
                parent_siblings,
                key=lambda task: (
                    task.state == _DONE_STATE,
                    task.id in append_ids,
                    task.sequence,
                    task.id,
                ),
            )
            # Avoid rewriting every sibling (and its write_date) when the
            # current sequence already represents the intended order.
            if all(
                previous.id == current.id
                for previous, current in zip(parent_siblings, desired)
            ) and all(
                previous.sequence < current.sequence
                for previous, current in zip(parent_siblings, parent_siblings[1:])
            ):
                continue

            for position, task in enumerate(desired, start=1):
                sequence = position * _SEQUENCE_STEP
                if task.sequence != sequence:
                    task.with_context(
                        **{
                            _REORDER_CONTEXT_KEY: True,
                            "tracking_disable": True,
                            "mail_notrack": True,
                        }
                    ).write({"sequence": sequence})

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        created_subtasks = tasks.filtered("parent_id")
        if created_subtasks and not self.env.context.get(_REORDER_CONTEXT_KEY):
            self._normalize_subtask_order(
                set(created_subtasks.mapped("parent_id").ids),
                created_subtasks.ids,
            )
        return tasks

    def write(self, vals):
        if self.env.context.get(_REORDER_CONTEXT_KEY) or not (
            {"state", "parent_id"} & vals.keys()
        ):
            return super().write(vals)

        original = {
            task.id: (task.parent_id.id, task.state == _DONE_STATE)
            for task in self
        }
        result = super().write(vals)

        affected_parents = set()
        appended = set()
        for task in self:
            previous_parent, previously_done = original[task.id]
            current_parent = task.parent_id.id
            now_done = task.state == _DONE_STATE
            if previous_parent != current_parent:
                if previous_parent:
                    affected_parents.add(previous_parent)
                if current_parent:
                    affected_parents.add(current_parent)
                    appended.add(task.id)
            elif previously_done != now_done and current_parent:
                affected_parents.add(current_parent)
                appended.add(task.id)

        if affected_parents:
            self._normalize_subtask_order(affected_parents, appended)
        return result
