"""One-time migration from sorting by (completed, sequence, id).

The view must now sort by (sequence, id), so move already completed subtasks
below active ones *once* on upgrade without changing their relative order.
Only the sequence column is changed; task IDs and parent relationships remain.
"""


def migrate(cr, version):
    cr.execute(
        """
        WITH ordered AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY parent_id
                    ORDER BY
                        CASE WHEN state = '1_done' THEN 1 ELSE 0 END,
                        sequence ASC,
                        id ASC
                ) * 10 AS new_sequence
            FROM project_task
            WHERE parent_id IS NOT NULL
        )
        UPDATE project_task AS task
           SET sequence = ordered.new_sequence
          FROM ordered
         WHERE task.id = ordered.id
           AND task.sequence IS DISTINCT FROM ordered.new_sequence
        """
    )
