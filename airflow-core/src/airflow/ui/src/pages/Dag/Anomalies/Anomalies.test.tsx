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
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { registerAnomaliesMswServerHooks } from "./Anomalies.test-msw-hooks";
import { server } from "./Anomalies.test-setup";
import { makeAnomaly, makeTask, makeTaskWithNullTaskId, renderAnomalies } from "./Anomalies.test-support";

registerAnomaliesMswServerHooks();

describe("Anomalies", () => {
  it("renders page title and description", async () => {
    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Task performance anomalies")).toBeInTheDocument());
    expect(
      screen.getByText("Tasks that ran faster or slower than normal are listed below."),
    ).toBeInTheDocument();
  });

  it("renders per-task section heading", async () => {
    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Per-task anomaly status")).toBeInTheDocument());
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
    await waitFor(() => expect(screen.getByText("No tasks found")).toBeInTheDocument());
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
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTaskWithNullTaskId("display-only")], total_entries: 1 }),
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
});
