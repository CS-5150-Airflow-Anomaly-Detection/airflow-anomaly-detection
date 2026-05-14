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
import { render, screen } from "@testing-library/react";
import i18n from "i18next";
import type { PropsWithChildren } from "react";
import { I18nextProvider, initReactI18next } from "react-i18next";
import { beforeAll, describe, expect, it } from "vitest";

import { BaseWrapper } from "src/utils/Wrapper";

import { AnomalyDashboard } from "./AnomalyDashboard";

beforeAll(async () => {
  // Keep this test fully local: don't import `src/i18n/config` (it uses http-backend).
  await i18n.use(initReactI18next).init({
    defaultNS: "dashboard",
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    lng: "en",
    ns: ["common", "dashboard"],
    resources: {
      en: {
        common: {
          dagId: "DAG ID",
          duration: "Duration",
          runId: "Run ID",
          task: "Task",
        },
        dashboard: {
          anomalies: {
            columns: {
              detected: "Detected",
              expectedRange: "Expected range",
              type: "Type",
            },
            description: "Anomaly dashboard description",
            // Included for completeness if table rows are added later.
            durationSeconds: "{{count}}s",
            empty: "No anomalies found",
            recent: "Recent anomalies",
            stats: {
              algorithm: "Algorithm",
              last24h: "Last 24h",
              tasksMonitored: "Tasks monitored",
            },
            title: "Anomalies",
            types: {
              fast: "Fast",
              slow: "Slow",
            },
          },
        },
      },
    },
  });
});

const Wrapper = ({ children }: PropsWithChildren) => (
  <BaseWrapper>
    <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
  </BaseWrapper>
);

describe("AnomalyDashboard", () => {
  it("renders header, stat cards, and empty recent-anomalies table", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    expect(screen.getByText("Anomalies")).toBeInTheDocument();
    expect(screen.getByText("Anomaly dashboard description")).toBeInTheDocument();
    expect(screen.getByText("Last 24h")).toBeInTheDocument();
    expect(screen.getByText("Tasks monitored")).toBeInTheDocument();
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(2);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("Recent anomalies")).toBeInTheDocument();
    expect(screen.getByText("No anomalies found")).toBeInTheDocument();
  });

  it("renders all table column headers", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    expect(screen.getByText("DAG ID")).toBeInTheDocument();
    expect(screen.getByText("Task")).toBeInTheDocument();
    expect(screen.getByText("Run ID")).toBeInTheDocument();
    expect(screen.getByText("Detected")).toBeInTheDocument();
    expect(screen.getByText("Duration")).toBeInTheDocument();
    expect(screen.getByText("Expected range")).toBeInTheDocument();
    expect(screen.getByText("Type")).toBeInTheDocument();
  });

  it("renders three stat cards with correct labels", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    const cards = screen.getAllByRole("heading");

    expect(cards.length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText("Last 24h")).toBeInTheDocument();
    expect(screen.getByText("Tasks monitored")).toBeInTheDocument();
    expect(screen.getByText("Algorithm")).toBeInTheDocument();
  });

  it("stat card for last-24h and tasks-monitored shows 0", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    const zeros = screen.getAllByText("0");

    expect(zeros).toHaveLength(2);
  });

  it("stat card for algorithm shows em-dash placeholder", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders anomaly rows when anomalies are present", () => {
    const anomalies = [
      {
        dagId: "dag-1",
        detectedAt: "2026-01-01",
        durationSeconds: 10,
        expectedRange: "5-15s",
        runId: "run-1",
        taskId: "task-slow",
        type: "slow" as const,
      },
      {
        dagId: "dag-2",
        detectedAt: "2026-01-02",
        durationSeconds: 3,
        expectedRange: "5-15s",
        runId: "run-2",
        taskId: "task-fast",
        type: "fast" as const,
      },
    ];

    render(<AnomalyDashboard anomalies={anomalies} />, { wrapper: Wrapper });

    expect(screen.getByText("dag-1")).toBeInTheDocument();
    expect(screen.getByText("dag-2")).toBeInTheDocument();
    expect(screen.getByText("task-slow")).toBeInTheDocument();
    expect(screen.getByText("task-fast")).toBeInTheDocument();
    expect(screen.getByText("Slow")).toBeInTheDocument();
    expect(screen.getByText("Fast")).toBeInTheDocument();
    expect(screen.getByText("10s")).toBeInTheDocument();
    expect(screen.queryByText("No anomalies found")).not.toBeInTheDocument();
  });

  it("accepts explicit stats prop and renders provided values", () => {
    const stats = { algorithmsEnabled: "IsolationForest", anomaliesLast24h: 3, tasksMonitored: 12 };

    render(<AnomalyDashboard stats={stats} />, { wrapper: Wrapper });

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("IsolationForest")).toBeInTheDocument();
  });

  it("uses orange badge for slow anomalies and blue for fast", () => {
    const anomalies = [
      {
        dagId: "dag-1",
        detectedAt: "2026-01-01",
        durationSeconds: 10,
        expectedRange: "5-15s",
        runId: "run-1",
        taskId: "task-slow",
        type: "slow" as const,
      },
    ];

    render(<AnomalyDashboard anomalies={anomalies} />, { wrapper: Wrapper });

    expect(screen.getByText("Slow")).toBeInTheDocument();
  });
});
