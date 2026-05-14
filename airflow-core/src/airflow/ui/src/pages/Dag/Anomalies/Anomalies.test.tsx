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
import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ChakraProvider, defaultSystem } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import i18n from "i18next";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import type { PropsWithChildren } from "react";
import { I18nextProvider, initReactI18next } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";

import type { TaskInstanceAnomalyResponse, TaskResponse } from "openapi-gen/requests/types.gen";
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

// -- MSW server -------------------------------------------------------------

const EMPTY_ANOMALY_RESPONSE = { task_instance_anomalies: [], total_entries: 0 };
const EMPTY_TASK_RESPONSE = { tasks: [], total_entries: 0 };

const server = setupServer(
  http.get("/api/v2/task_instance_anomaly", () => HttpResponse.json(EMPTY_ANOMALY_RESPONSE)),
  http.get("/api/v2/dags/:dagId/tasks", () => HttpResponse.json(EMPTY_TASK_RESPONSE)),
  http.get("/ui/grid/structure/:dagId", () => HttpResponse.json([])),
);

beforeAll(async () => {
  server.listen({ onUnhandledRequest: "bypass" });

  await i18n.use(initReactI18next).init({
    defaultNS: "dag",
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    lng: "en",
    ns: ["common", "dag"],
    resources: {
      en: {
        common: { task: "Task" },
        dag: {
          anomalies: {
            columns: {
              detector: "Detector",
              firstDetected: "First detected",
              lastUpdated: "Last updated",
              reason: "Reason",
              status: "Status",
            },
            description: "Tasks that ran faster or slower than normal are listed below.",
            emptyTasks: "No tasks found",
            loadError: "Failed to load anomaly data",
            perTaskStatus: "Per-task anomaly status",
            statuses: { anomalous: "Anomalous", normal: "Normal" },
            title: "Task performance anomalies",
          },
        },
      },
    },
  });
});

afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// -- render helper ----------------------------------------------------------

const makeQueryClient = (retry = false) =>
  new QueryClient({ defaultOptions: { queries: { retry, staleTime: Infinity } } });

const renderAnomalies = (dagId = "test-dag", queryClient = makeQueryClient()) =>
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

// -- mock data factories ----------------------------------------------------

const makeAnomaly = (overrides?: Partial<TaskInstanceAnomalyResponse>): TaskInstanceAnomalyResponse => ({
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

const makeTask = (taskId: string): TaskResponse => ({
  class_ref: null,
  depends_on_past: false,
  doc_md: null,
  downstream_task_ids: null,
  end_date: null,
  execution_timeout: null,
  extra_links: [],
  is_mapped: false,
  operator_name: null,
  owner: null,
  params: null,
  pool: null,
  pool_slots: null,
  priority_weight: null,
  queue: null,
  retries: null,
  retry_delay: null,
  retry_exponential_backoff: 0,
  start_date: null,
  task_display_name: taskId,
  task_id: taskId,
  template_fields: null,
  trigger_rule: null,
  ui_color: null,
  ui_fgcolor: null,
  wait_for_downstream: false,
  weight_rule: null,
});

// -- tests ------------------------------------------------------------------

describe("Anomalies", () => {
  it("renders page title and description", async () => {
    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("Task performance anomalies")).toBeInTheDocument(),
    );
    expect(
      screen.getByText("Tasks that ran faster or slower than normal are listed below."),
    ).toBeInTheDocument();
  });

  it("renders per-task section heading", async () => {
    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("Per-task anomaly status")).toBeInTheDocument(),
    );
  });

  it("renders all table column headers", async () => {
    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Task")).toBeInTheDocument());
    expect(screen.getByText("First detected")).toBeInTheDocument();
    expect(screen.getByText("Last updated")).toBeInTheDocument();
    expect(screen.getByText("Detector")).toBeInTheDocument();
    expect(screen.getByText("Reason")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("renders empty state message when no tasks are found", async () => {
    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("No tasks found")).toBeInTheDocument(),
    );
  });

  it("renders Normal badge when task has no anomaly records", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Normal")).toBeInTheDocument());
    expect(screen.queryByText("Anomalous")).not.toBeInTheDocument();
  });

  it("renders Anomalous badge when latest anomaly record is anomalous", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly()],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Anomalous")).toBeInTheDocument());
    expect(screen.queryByText("Normal")).not.toBeInTheDocument();
  });

  it("renders Normal badge when latest anomaly record is not anomalous", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ is_anomalous: false })],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Normal")).toBeInTheDocument());
  });

  it("renders task name as a link with correct URL when task_id is present", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByRole("link", { name: "task-1" })).toBeInTheDocument());

    const link = screen.getByRole("link", { name: "task-1" });

    expect(link).toHaveAttribute("href", "/dags/test-dag/tasks/task-1/task_anomalies");
  });

  it("renders task display name as plain text when task_id is null", async () => {
    const taskWithNullId: TaskResponse = { ...makeTask("display-only"), task_id: null };

    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [taskWithNullId], total_entries: 1 }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("display-only")).toBeInTheDocument());
    expect(screen.queryByRole("link", { name: "display-only" })).not.toBeInTheDocument();
  });

  it("shows em-dash placeholders when task has no anomaly records", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
    );

    renderAnomalies();
    await waitFor(() => {
      const dashes = screen.getAllByText("—");

      expect(dashes.length).toBeGreaterThanOrEqual(4);
    });
  });

  it("shows explicit reason when anomaly record has a non-empty reason", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ reason: "Runtime outside threshold." })],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("Runtime outside threshold.")).toBeInTheDocument(),
    );
  });

  it("shows ThresholdAnomaly fallback reason when reason is null", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [
            makeAnomaly({ detector_name: "ThresholdAnomaly", reason: null }),
          ],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() =>
      expect(
        screen.getByText(
          "Latest task runtime fell outside the configured min/max threshold for the historical window.",
        ),
      ).toBeInTheDocument(),
    );
  });

  it("shows AlwaysAnomaly fallback reason when reason is null", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ detector_name: "AlwaysAnomaly", reason: null })],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() =>
      expect(
        screen.getByText("Detector is configured to flag every run (typically for testing)."),
      ).toBeInTheDocument(),
    );
  });

  it("shows generic fallback reason for unknown detector when reason is null", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [
            makeAnomaly({ detector_name: "UnknownDetector", reason: null }),
          ],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("Flagged by detector UnknownDetector.")).toBeInTheDocument(),
    );
  });

  it("shows error message when anomaly API returns an error", async () => {
    server.use(
      http.get("/api/v2/task_instance_anomaly", () => new HttpResponse(null, { status: 500 })),
    );

    renderAnomalies("test-dag", makeQueryClient(false));
    await waitFor(() =>
      expect(screen.getByText("Failed to load anomaly data")).toBeInTheDocument(),
    );
  });

  it("renders multiple tasks in the table", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({
          tasks: [makeTask("task-a"), makeTask("task-b"), makeTask("task-c")],
          total_entries: 3,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("task-a")).toBeInTheDocument());
    expect(screen.getByText("task-b")).toBeInTheDocument();
    expect(screen.getByText("task-c")).toBeInTheDocument();
  });

  it("shows detector name in the table row", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ detector_name: "ThresholdAnomaly" })],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() =>
      expect(screen.getByText("ThresholdAnomaly")).toBeInTheDocument(),
    );
  });
});
