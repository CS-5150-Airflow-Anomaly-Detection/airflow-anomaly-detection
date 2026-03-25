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
import {
  Badge,
  Box,
  Flex,
  Heading,
  Skeleton,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react";
import { FiAlertTriangle } from "react-icons/fi";
import { useParams } from "react-router-dom";

import {
  useTaskInstanceAnomalyServiceGetTaskInstanceAnomalies,
  useTaskServiceGetTasks,
} from "openapi/queries";
import Time from "src/components/Time";
import { useOpenGroups } from "src/context/openGroups";
import { useGridStructure } from "src/queries/useGridStructure.ts";
import { flattenNodes } from "src/layouts/Details/Grid/utils";

import type { TaskInstanceAnomalyResponse } from "openapi/requests/types.gen";

/** When the API omits `reason`, show a human-readable line derived from `detector_name` (UI-only). */
const getTaskAnomalyReasonDisplay = (anomaly: TaskInstanceAnomalyResponse): string => {
  const trimmed = anomaly.reason?.trim();

  if (trimmed !== undefined && trimmed !== "") {
    return trimmed;
  }

  const { detector_name: detectorName } = anomaly;
  const fallbackByDetector: Record<string, string> = {
    AlwaysAnomaly: "Detector is configured to flag every run (typically for testing).",
    ThresholdAnomaly:
      "Latest task runtime fell outside the configured min/max threshold for the historical window.",
  };

  return fallbackByDetector[detectorName] ?? `Flagged by detector ${detectorName}.`;
};

export const Anomalies = () => {
  const { dagId = "" } = useParams();

  const { data: anomalyData, isLoading: isLoadingAnomalies, error } =
    useTaskInstanceAnomalyServiceGetTaskInstanceAnomalies(
      {
        dagId: dagId || undefined,
        limit: 500,
        offset: 0,
      },
      undefined,
      {
        enabled: Boolean(dagId),
        refetchInterval: 3000,
        refetchOnWindowFocus: true,
      },
    );

  const { data: tasksData, isLoading: isLoadingTasks } = useTaskServiceGetTasks(
    { dagId: dagId || "" },
    undefined,
    { enabled: !!dagId },
  );

  const { openGroupIds } = useOpenGroups();
  const { data: dagStructure } = useGridStructure({ limit: 1 });
  const { flatNodes } = flattenNodes(dagStructure, openGroupIds);
  const gridOrderIndex = new Map(flatNodes.map((node, i) => [node.id, i]));

  const allAnomalies = anomalyData?.task_instance_anomalies ?? [];
  const anomaliesByTaskId = new Map<string, typeof allAnomalies>();
  for (const anomaly of allAnomalies) {
    const taskAnomalies = anomaliesByTaskId.get(anomaly.task_id);
    if (taskAnomalies) {
      taskAnomalies.push(anomaly);
    } else {
      anomaliesByTaskId.set(anomaly.task_id, [anomaly]);
    }
  }

  const tasksRaw = tasksData?.tasks ?? [];
  const tasks = [...tasksRaw].sort((a, b) => {
    const idA = a.task_id ?? a.task_display_name ?? "";
    const idB = b.task_id ?? b.task_display_name ?? "";
    return (gridOrderIndex.get(idA) ?? 999) - (gridOrderIndex.get(idB) ?? 999);
  });
  const isLoading = isLoadingAnomalies || isLoadingTasks;

  const titleText = "Task performance anomalies";

  return (
    <Box overflow="auto" px={{ base: 2, md: 4 }}>
      <VStack alignItems="stretch" gap={6}>
        <Flex alignItems="center" gap={2}>
          <Box color="orange.500">
            <FiAlertTriangle size={24} />
          </Box>
          <Heading size="lg">{titleText}</Heading>
        </Flex>

        <Text color="fg.muted" fontSize="sm">
          Tasks in this DAG that ran significantly faster or slower than their
          historical baselines are listed below. Use this to spot performance
          regressions or unexpected speedups.
        </Text>

        <Box>
          <Heading mb={3} size="sm">
            Per-task anomaly status
          </Heading>

          {Boolean(error) && (
            <Text color="fg.error" mb={3}>
              Failed to load anomalies. Please try again.
            </Text>
          )}

          {isLoading ? (
            <Skeleton height="200px" borderRadius="md" />
          ) : (
            <Table.Root size="sm" striped>
              <Table.Header bg="chakra-body-bg" position="sticky" top={0} zIndex={1}>
                <Table.Row>
                  <Table.ColumnHeader>Task</Table.ColumnHeader>
                  <Table.ColumnHeader>First detected</Table.ColumnHeader>
                  <Table.ColumnHeader>Last updated</Table.ColumnHeader>
                  <Table.ColumnHeader>Detector</Table.ColumnHeader>
                  <Table.ColumnHeader>Reason</Table.ColumnHeader>
                  <Table.ColumnHeader>Status</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {tasks.length === 0 ? (
                  <Table.Row>
                    <Table.Cell colSpan={6} py={8} textAlign="center">
                      <Text color="fg.muted">
                        No tasks in this DAG.
                      </Text>
                    </Table.Cell>
                  </Table.Row>
                ) : (
                  tasks.map((task) => {
                    const taskId = task.task_id ?? "";
                    const taskAnomalies = taskId ? (anomaliesByTaskId.get(taskId) ?? []) : [];
                    const anomaliesByTime = [...taskAnomalies].sort(
                      (a, b) =>
                        new Date(a.created_at).getTime() -
                        new Date(b.created_at).getTime(),
                    );
                    const firstAnomaly = anomaliesByTime[0] ?? null;
                    const latestAnomaly =
                      anomaliesByTime[anomaliesByTime.length - 1] ?? null;
                    const isAnomalous = latestAnomaly?.is_anomalous ?? false;

                    return (
                      <Table.Row key={task.task_id ?? task.task_display_name ?? ""}>
                        <Table.Cell>
                          {task.task_display_name ?? task.task_id ?? "—"}
                        </Table.Cell>
                        <Table.Cell>
                          {firstAnomaly ? (
                            <Time datetime={firstAnomaly.created_at} />
                          ) : (
                            "—"
                          )}
                        </Table.Cell>
                        <Table.Cell>
                          {latestAnomaly ? (
                            <Time datetime={latestAnomaly.updated_at} />
                          ) : (
                            "—"
                          )}
                        </Table.Cell>
                        <Table.Cell>
                          {latestAnomaly?.detector_name ?? "—"}
                        </Table.Cell>
                        <Table.Cell>
                          {latestAnomaly ? getTaskAnomalyReasonDisplay(latestAnomaly) : "—"}
                        </Table.Cell>
                        <Table.Cell>
                          {isAnomalous ? (
                            <Badge colorPalette="orange" size="sm">
                              Anomalous
                            </Badge>
                          ) : (
                            <Badge colorPalette="green" size="sm">
                              normal
                            </Badge>
                          )}
                        </Table.Cell>
                      </Table.Row>
                    );
                  })
                )}
              </Table.Body>
            </Table.Root>
          )}
        </Box>
      </VStack>
    </Box>
  );
};
