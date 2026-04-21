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
import { Link as RouterLink } from "react-router-dom";

import { DataTable } from "src/components/DataTable";
import { useTableURLState } from "src/components/DataTable/useTableUrlState";
import { TruncatedText } from "src/components/TruncatedText";
import Time from "src/components/Time";
import { renderDuration } from "src/utils";
import { getTaskInstanceLink } from "src/utils/links";

export type TaskAnomalyRow = {
  anomaly_alg_result: string;
  anomaly_algorithm: string;
  dag_id: string;
  dag_run_id: string;
  duration: number | null;
  historic_equal_map_index: boolean;
  historic_runs_used: number;
  id: string;
  map_index: number;
  run_after: string;
  start_date: string | null;
  task_id: string;
};

const taskAnomalyColumns = (translate: TFunction): Array<ColumnDef<TaskAnomalyRow>> => [
  {
    accessorKey: "run_after",
    cell: ({ row: { original } }) => (
      <Link asChild color="fg.info" fontWeight="bold">
        <RouterLink
          to={getTaskInstanceLink({
            dagId: original.dag_id,
            dagRunId: original.dag_run_id,
            mapIndex: original.map_index,
            taskId: original.task_id,
          })}
        >
          <Time datetime={original.run_after} />
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
    accessorKey: "anomaly_algorithm",
    cell: ({ row: { original } }) => <TruncatedText text={original.anomaly_algorithm} />,
    header: translate("taskAnomalies.anomalyAlgorithm"),
  },
  {
    accessorKey: "anomaly_alg_result",
    cell: ({ row: { original } }) => <TruncatedText text={original.anomaly_alg_result} />,
    header: translate("taskAnomalies.anomalyAlgResult"),
  },
  {
    accessorKey: "historic_runs_used",
    header: translate("taskAnomalies.historicRunsUsed"),
  },
  {
    accessorKey: "historic_equal_map_index",
    cell: ({ row: { original } }) =>
      original.historic_equal_map_index
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
  const { setTableURLState, tableURLState } = useTableURLState();

  const columns = useMemo(() => taskAnomalyColumns(translate), [translate]);

  return (
    <DataTable
      columns={columns}
      data={[]}
      initialState={tableURLState}
      isLoading={false}
      modelName="common:taskAnomaly"
      onStateChange={setTableURLState}
      rowCountHeadingRender={(count) => translate("taskAnomalies.detectedCount", { count })}
      showTableWhenEmpty
      total={0}
    />
  );
};
