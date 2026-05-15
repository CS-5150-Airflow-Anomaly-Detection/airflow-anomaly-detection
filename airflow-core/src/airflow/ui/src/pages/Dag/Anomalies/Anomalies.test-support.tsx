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
import { ChakraProvider, defaultSystem } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import i18n from "i18next";
import type { TaskInstanceAnomalyResponse, TaskResponse } from "openapi-gen/requests/types.gen";
import type { PropsWithChildren } from "react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { OpenGroupsContext } from "src/context/openGroups/Context";
import type { OpenGroupsContextType } from "src/context/openGroups/Context";
import { TimezoneProvider } from "src/context/timezone";

import { Anomalies } from "./Anomalies";

const OPEN_GROUPS_VALUE: OpenGroupsContextType = {
  allGroupIds: [],
  openGroupIds: [],
  setAllGroupIds: () => undefined,
  setOpenGroupIds: () => undefined,
  toggleGroupId: () => undefined,
};

export const makeQueryClient = (retry = false) =>
  new QueryClient({ defaultOptions: { queries: { retry, staleTime: Infinity } } });

export const renderAnomalies = (dagId = "test-dag", queryClient = makeQueryClient()) =>
  render(
    <MemoryRouter initialEntries={[`/dags/${dagId}`]}>
      <Routes>
        <Route element={<Anomalies />} path="/dags/:dagId" />
      </Routes>
    </MemoryRouter>,
    {
      wrapper: ({ children }: PropsWithChildren) => (
        <ChakraProvider value={defaultSystem}>
          <QueryClientProvider client={queryClient}>
            <TimezoneProvider>
              <OpenGroupsContext.Provider value={OPEN_GROUPS_VALUE}>
                <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
              </OpenGroupsContext.Provider>
            </TimezoneProvider>
          </QueryClientProvider>
        </ChakraProvider>
      ),
    },
  );

export const makeAnomaly = (
  overrides?: Partial<TaskInstanceAnomalyResponse>,
): TaskInstanceAnomalyResponse => ({
  created_at: "2026-01-01T10:00:00Z",
  dag_id: "test-dag",
  detector_name: "ThresholdAnomaly",
  duration: 30.5,
  historic_runs_count: 10,
  id: 1,
  is_anomalous: true,
  map_index: -1,
  reason: "Runtime outside threshold.",
  run_id: "run-1",
  start_date: "2026-01-01T10:00:00Z",
  task_id: "task-1",
  try_number: 1,
  updated_at: "2026-01-02T10:00:00Z",
  used_equal_map_index: false,
  ...overrides,
});

export const makeTask = (taskId: string): TaskResponse =>
  ({
    class_ref: undefined,
    depends_on_past: false,
    doc_md: undefined,
    downstream_task_ids: undefined,
    end_date: undefined,
    execution_timeout: undefined,
    extra_links: [],
    is_mapped: false,
    operator_name: undefined,
    owner: undefined,
    params: undefined,
    pool: undefined,
    pool_slots: undefined,
    priority_weight: undefined,
    queue: undefined,
    retries: undefined,
    retry_delay: undefined,
    retry_exponential_backoff: 0,
    start_date: undefined,
    task_display_name: taskId,
    task_id: taskId,
    template_fields: undefined,
    trigger_rule: undefined,
    ui_color: undefined,
    ui_fgcolor: undefined,
    wait_for_downstream: false,
    weight_rule: undefined,
  }) as unknown as TaskResponse;

/** Mirrors API rows that expose a display name without a concrete task id. */
export const makeTaskWithNullTaskId = (taskDisplayName: string): TaskResponse =>
  ({
    ...makeTask(taskDisplayName),
    // eslint-disable-next-line unicorn/no-null -- OpenAPI type is `string | null`
    task_id: null,
  }) as unknown as TaskResponse;
