from odoo.tests.common import TransactionCase


class TestSubtaskOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "Progress & Sequence"})
        cls.parent = cls.env["project.task"].create({
            "name": "Parent task",
            "project_id": cls.project.id,
        })

    def _child(self, name):
        return self.env["project.task"].create({
            "name": name,
            "parent_id": self.parent.id,
            "project_id": self.project.id,
        })

    def _ordered_ids(self):
        self.env["project.task"].flush_model(["sequence", "state", "parent_id"])
        return self.env["project.task"].search(
            [("parent_id", "=", self.parent.id)],
            order="sequence asc, id asc",
        ).ids

    def test_manual_reordering_does_not_change_ids(self):
        a, b, c = (self._child(name) for name in ("A", "B", "C"))
        initial_ids = {a.id, b.id, c.id}
        # Mirrors a manual change to the sequence handle: NO state update.
        c.write({"sequence": 1})
        self.assertEqual(self._ordered_ids(), [c.id, a.id, b.id])
        self.assertEqual({a.id, b.id, c.id}, initial_ids)
        # Simulate re-reading from the database after reloading the task.
        (a | b | c).invalidate_recordset(["sequence"])
        self.assertEqual(self._ordered_ids(), [c.id, a.id, b.id])

    def test_completed_goes_to_end_and_reopen_after_open(self):
        a, b, c = (self._child(name) for name in ("A", "B", "C"))
        b.write({"state": "1_done"})
        self.assertEqual(self._ordered_ids(), [a.id, c.id, b.id])
        a.write({"state": "1_done"})
        self.assertEqual(self._ordered_ids(), [c.id, b.id, a.id])
        b.write({"state": "01_in_progress"})
        self.assertEqual(self._ordered_ids(), [c.id, b.id, a.id])

    def test_new_open_subtask_precedes_completed(self):
        a, b = (self._child(name) for name in ("A", "B"))
        a.write({"state": "1_done"})
        c = self._child("C")
        self.assertEqual(self._ordered_ids(), [b.id, c.id, a.id])

    def test_manual_drag_does_not_trigger_auto_grouping(self):
        a, b = (self._child(name) for name in ("A", "B"))
        a.write({"state": "1_done"})
        a.write({"sequence": 1})
        # Explicit manual drag has precedence until a completion/parent
        # change or a new sibling creation causes an automatic regrouping.
        self.assertEqual(self._ordered_ids(), [a.id, b.id])
