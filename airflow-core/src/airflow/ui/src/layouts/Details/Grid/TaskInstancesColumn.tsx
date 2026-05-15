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
import { Box } from "@chakra-ui/react";
import type { VirtualItem } from "@tanstack/react-virtual";
import { useParams } from "react-router-dom";

import type { GridRunsResponse } from "openapi/requests";
import type { LightGridTaskInstanceSummary } from "openapi/requests/types.gen";
import { useHover } from "src/context/hover";
import { useGridTiSummaries } from "src/queries/useGridTISummaries.ts";

import { GridTI } from "./GridTI";
import type { GridTask } from "./utils";

const isTaskCellAnomalous = (keys: Set<string>, runId: string, taskId: string) => {
  if (keys.has(`${runId}::${taskId}::-1`)) {
    return true;
  }
  const prefix = `${runId}::${taskId}::`;

  for (const key of keys) {
    if (key.startsWith(prefix)) {
      return true;
    }
  }

  return false;
};

const getDetectorForCell = (
  detectors: Map<string, string>,
  runId: string,
  taskId: string,
): string | undefined => {
  const exact = `${runId}::${taskId}::-1`;

  if (detectors.has(exact)) {
    return detectors.get(exact);
  }
  const prefix = `${runId}::${taskId}::`;

  for (const [key, name] of detectors) {
    if (key.startsWith(prefix)) {
      return name;
    }
  }

  return undefined;
};

type Props = {
  readonly anomalousCellKeys: Set<string>;
  readonly anomalousDetectorByCellKey: Map<string, string>;
  readonly nodes: Array<GridTask>;
  readonly onCellClick?: () => void;
  readonly run: GridRunsResponse;
  readonly virtualItems?: Array<VirtualItem>;
};

const ROW_HEIGHT = 20;

export const TaskInstancesColumn = ({
  anomalousCellKeys,
  anomalousDetectorByCellKey,
  nodes,
  onCellClick,
  run,
  virtualItems,
}: Props) => {
  const { dagId = "", runId } = useParams();
  const { data: gridTISummaries } = useGridTiSummaries({ dagId, runId: run.run_id, state: run.state });
  const { hoveredRunId, setHoveredRunId } = useHover();

  const itemsToRender =
    virtualItems ?? nodes.map((_, index) => ({ index, size: ROW_HEIGHT, start: index * ROW_HEIGHT }));

  const taskInstances = gridTISummaries?.task_instances ?? [];
  const taskInstanceMap = new Map<string, LightGridTaskInstanceSummary>();

  for (const ti of taskInstances) {
    taskInstanceMap.set(ti.task_id, ti);
  }

  const isSelected = runId === run.run_id;
  const isHovered = hoveredRunId === run.run_id;

  const handleMouseEnter = () => setHoveredRunId(run.run_id);
  const handleMouseLeave = () => setHoveredRunId(undefined);

  return (
    <Box
      bg={isSelected ? "brand.emphasized" : isHovered ? "brand.muted" : undefined}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      position="relative"
      transition="background-color 0.2s"
      width="18px"
    >
      {itemsToRender.map((virtualItem) => {
        const node = nodes[virtualItem.index];

        if (!node) {
          return undefined;
        }

        const taskInstance = taskInstanceMap.get(node.id);

        if (!taskInstance) {
          return (
            <Box
              height={`${ROW_HEIGHT}px`}
              key={`${node.id}-${run.run_id}`}
              left={0}
              position="absolute"
              top={0}
              transform={`translateY(${virtualItem.start}px)`}
              width="18px"
            />
          );
        }

        const cellAnomalous = isTaskCellAnomalous(anomalousCellKeys, run.run_id, node.id);

        return (
          <Box
            key={node.id}
            left={0}
            position="absolute"
            top={0}
            transform={`translateY(${virtualItem.start}px)`}
          >
            <GridTI
              anomalyDetectorName={
                cellAnomalous
                  ? getDetectorForCell(anomalousDetectorByCellKey, run.run_id, node.id)
                  : undefined
              }
              dagId={dagId}
              instance={taskInstance}
              isAnomalous={cellAnomalous}
              isGroup={node.isGroup}
              isMapped={node.is_mapped}
              label={node.label}
              onClick={onCellClick}
              runId={run.run_id}
              taskId={node.id}
            />
          </Box>
        );
      })}
    </Box>
  );
};
