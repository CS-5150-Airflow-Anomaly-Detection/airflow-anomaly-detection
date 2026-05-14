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
import i18n from "i18next";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { initReactI18next } from "react-i18next";

export const EMPTY_ANOMALY_RESPONSE = { task_instance_anomalies: [], total_entries: 0 };
export const EMPTY_TASK_RESPONSE = { tasks: [], total_entries: 0 };

export const server = setupServer(
  http.get("/api/v2/task_instance_anomaly", () => HttpResponse.json(EMPTY_ANOMALY_RESPONSE)),
  http.get("/api/v2/dags/:dagId/tasks", () => HttpResponse.json(EMPTY_TASK_RESPONSE)),
  http.get("/ui/grid/structure/:dagId", () => HttpResponse.json([])),
);

export const initAnomaliesTestI18n = async function initAnomaliesTestI18n(): Promise<void> {
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
};
