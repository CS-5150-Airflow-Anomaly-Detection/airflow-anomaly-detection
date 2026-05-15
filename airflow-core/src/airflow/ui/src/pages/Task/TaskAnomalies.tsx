/*!
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { Link } from "@chakra-ui/react";
import type { ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useTaskInstanceAnomalyServiceGetTaskInstanceAnomalies } from "openapi/queries";
import type { TaskInstanceAnomalyResponse } from "openapi/requests/types.gen";
import { DataTable } from "src/components/DataTable";
import { useTableURLState } from "src/components/DataTable/useTableUrlState";
import { ErrorAlert } from "src/components/ErrorAlert";
import Time from "src/components/Time";
import { TruncatedText } from "src/components/TruncatedText";
import { renderDuration } from "src/utils";
import { getTaskInstanceLink } from "src/utils/links";

const taskAnomalyColumns = (translate: TFunction): Array<ColumnDef<TaskInstanceAnomalyResponse>> => [
  {
    accessorKey: "run_id",
    cell: ({ row: { original } }) => (
      <Link asChild color="fg.info" fontWeight="bold">
        <RouterLink
          to={getTaskInstanceLink({
            dagId: original.dag_id,
            dagRunId: original.run_id,
            mapIndex: original.map_index,
            taskId: original.task_id,
          })}
        >
          <TruncatedText maxWidth="320px" minWidth={0} text={original.run_id} />
        </RouterLink>
      </Link>
    ),
    header: translate("dagRun_one"),
  },
  {
    accessorKey: "map_index",
    header: translate("mapIndex"),
  },
  {
    accessorKey: "detector_name",
    cell: ({ row: { original } }) => <TruncatedText minWidth={0} text={original.detector_name} />,
    header: translate("taskAnomalies.anomalyAlgorithm"),
  },
  {
    accessorKey: "is_anomalous",
    cell: ({ row: { original } }) =>
      original.is_anomalous
        ? translate("taskAnomalies.historicEqualMapIndexYes")
        : translate("taskAnomalies.historicEqualMapIndexNo"),
    header: translate("taskAnomalies.anomalyAlgResult"),
  },
  {
    accessorKey: "historic_runs_count",
    header: translate("taskAnomalies.historicRunsUsed"),
  },
  {
    accessorKey: "used_equal_map_index",
    cell: ({ row: { original } }) =>
      original.used_equal_map_index
        ? translate("taskAnomalies.historicEqualMapIndexYes")
        : translate("taskAnomalies.historicEqualMapIndexNo"),
    header: translate("taskAnomalies.historicEqualMapIndex"),
  },
  {
    accessorKey: "start_date",
    cell: ({ row: { original } }) => <Time datetime={original.start_date} />,
    header: translate("startDate"),
  },
  {
    accessorKey: "duration",
    cell: ({ row: { original } }) => renderDuration(original.duration),
    header: translate("duration"),
  },
];

export const TaskAnomalies = () => {
  const { t: translate } = useTranslation();
  const { dagId, taskId } = useParams();
  const { setTableURLState, tableURLState } = useTableURLState();
  const { pagination } = tableURLState;
  const { pageIndex, pageSize } = pagination;
  const shouldFetchTaskAnomalies = dagId !== undefined && dagId !== "" && dagId !== "~";

  const columns = useMemo(() => taskAnomalyColumns(translate), [translate]);
  const { data, error, isLoading } = useTaskInstanceAnomalyServiceGetTaskInstanceAnomalies(
    {
      dagId: shouldFetchTaskAnomalies ? dagId : undefined,
      limit: pageSize,
      offset: pageIndex * pageSize,
      taskId: taskId !== undefined && taskId !== "" && taskId !== "~" ? taskId : undefined,
    },
    undefined,
    {
      enabled: shouldFetchTaskAnomalies,
    },
  );

  return (
    <DataTable
      columns={columns}
      data={data?.task_instance_anomalies ?? []}
      errorMessage={<ErrorAlert error={error} />}
      initialState={tableURLState}
      isLoading={isLoading}
      modelName="common:taskAnomaly"
      onStateChange={setTableURLState}
      rowCountHeadingRender={(count) => translate("taskAnomalies.detectedCount", { count })}
      showTableWhenEmpty
      total={data?.total_entries}
    />
  );
};
