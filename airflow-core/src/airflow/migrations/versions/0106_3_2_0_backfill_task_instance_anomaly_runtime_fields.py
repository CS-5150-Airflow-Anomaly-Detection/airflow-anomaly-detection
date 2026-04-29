#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Backfill task instance anomaly runtime fields.

Revision ID: f1d4a3d8c9e2
Revises: c7f2cf4d20b1
Create Date: 2026-04-22 13:15:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1d4a3d8c9e2"
down_revision = "c7f2cf4d20b1"
branch_labels = None
depends_on = None
airflow_version = "3.2.0"


def upgrade():
    """Backfill start_date and duration in task_instance_anomaly from task_instance."""
    op.execute(
        """
        UPDATE task_instance_anomaly AS tia
        SET
            start_date = (
                SELECT ti.start_date
                FROM task_instance AS ti
                WHERE ti.dag_id = tia.dag_id
                  AND ti.run_id = tia.run_id
                  AND ti.task_id = tia.task_id
                  AND ti.map_index = tia.map_index
                  AND ti.try_number = tia.try_number
                LIMIT 1
            ),
            duration = (
                SELECT ti.duration
                FROM task_instance AS ti
                WHERE ti.dag_id = tia.dag_id
                  AND ti.run_id = tia.run_id
                  AND ti.task_id = tia.task_id
                  AND ti.map_index = tia.map_index
                  AND ti.try_number = tia.try_number
                LIMIT 1
            )
        WHERE tia.start_date IS NULL
           OR tia.duration IS NULL
        """
    )


def downgrade():
    """No-op downgrade for data backfill migration."""
