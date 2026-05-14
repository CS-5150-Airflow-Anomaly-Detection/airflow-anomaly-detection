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
import { makeAnomaly, makeQueryClient, makeTask, renderAnomalies } from "./Anomalies.test-support";

registerAnomaliesMswServerHooks();

describe("Anomalies reason display and errors", () => {
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
    await waitFor(() => expect(screen.getByText("Runtime outside threshold.")).toBeInTheDocument());
  });

  it("shows ThresholdAnomaly fallback when reason is absent", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ detector_name: "ThresholdAnomaly", reason: undefined })],
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

  it("shows AlwaysAnomaly fallback when reason is absent", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ detector_name: "AlwaysAnomaly", reason: undefined })],
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

  it("shows generic fallback for unknown detector when reason is absent", async () => {
    server.use(
      http.get("/api/v2/dags/:dagId/tasks", () =>
        HttpResponse.json({ tasks: [makeTask("task-1")], total_entries: 1 }),
      ),
      http.get("/api/v2/task_instance_anomaly", () =>
        HttpResponse.json({
          task_instance_anomalies: [makeAnomaly({ detector_name: "UnknownDetector", reason: undefined })],
          total_entries: 1,
        }),
      ),
    );

    renderAnomalies();
    await waitFor(() => expect(screen.getByText("Flagged by detector UnknownDetector.")).toBeInTheDocument());
  });

  it("shows error message when anomaly API returns an error", async () => {
    server.use(http.get("/api/v2/task_instance_anomaly", () => new HttpResponse(null, { status: 500 })));

    renderAnomalies("test-dag", makeQueryClient(false));
    await waitFor(() => expect(screen.getByText("Failed to load anomaly data")).toBeInTheDocument());
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
    await waitFor(() => expect(screen.getByText("ThresholdAnomaly")).toBeInTheDocument());
  });
});
