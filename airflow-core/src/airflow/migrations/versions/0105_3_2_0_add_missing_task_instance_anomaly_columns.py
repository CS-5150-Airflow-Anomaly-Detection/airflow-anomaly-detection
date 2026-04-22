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
Add missing task instance anomaly columns.

Revision ID: c7f2cf4d20b1
Revises: 438ed3578bfb
Create Date: 2026-04-22 13:08:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from airflow.utils.sqlalchemy import UtcDateTime

# revision identifiers, used by Alembic.
revision = "c7f2cf4d20b1"
down_revision = "438ed3578bfb"
branch_labels = None
depends_on = None
airflow_version = "3.2.0"


def upgrade():
    """Add missing columns to task_instance_anomaly."""
    op.add_column(
        "task_instance_anomaly",
        sa.Column("historic_runs_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "task_instance_anomaly",
        sa.Column("used_equal_map_index", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column("task_instance_anomaly", sa.Column("duration", sa.Float(), nullable=True))
    op.add_column("task_instance_anomaly", sa.Column("start_date", UtcDateTime(timezone=True), nullable=True))


def downgrade():
    """Remove added columns from task_instance_anomaly."""
    op.drop_column("task_instance_anomaly", "start_date")
    op.drop_column("task_instance_anomaly", "duration")
    op.drop_column("task_instance_anomaly", "used_equal_map_index")
    op.drop_column("task_instance_anomaly", "historic_runs_count")
