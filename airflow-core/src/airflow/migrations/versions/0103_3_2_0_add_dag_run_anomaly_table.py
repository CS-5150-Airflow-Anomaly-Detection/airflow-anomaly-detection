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
Add dag_run_anomaly table.

Revision ID: 7e8e6d53a4b2
Revises: 53ff648b8a26
Create Date: 2026-03-07 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from airflow._shared.timezones import timezone
from airflow.utils.sqlalchemy import UtcDateTime

# revision identifiers, used by Alembic.
revision = "7e8e6d53a4b2"
down_revision = "53ff648b8a26"
branch_labels = None
depends_on = None
airflow_version = "3.2.0"


def upgrade():
    """Create dag_run_anomaly table."""
    op.create_table(
        "dag_run_anomaly",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dag_id", sa.String(length=250), nullable=False),
        sa.Column("run_id", sa.String(length=250), nullable=False),
        sa.Column("is_anomalous", sa.Boolean(), nullable=False, default=False),
        sa.Column("detector_name", sa.String(length=100), nullable=False, default="always_true"),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", UtcDateTime(timezone=True), nullable=False, default=timezone.utcnow),
        sa.Column("updated_at", UtcDateTime(timezone=True), nullable=False, default=timezone.utcnow),
        sa.UniqueConstraint(
            "dag_id",
            "run_id",
            name="uq_dag_run_anomaly_dag_id_run_id",
        ),
    )


def downgrade():
    """Drop dag_run_anomaly table."""
    op.drop_table("dag_run_anomaly", if_exists=True)
