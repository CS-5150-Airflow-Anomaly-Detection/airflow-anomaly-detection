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
import type { PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";

import { BaseWrapper } from "src/utils/Wrapper";

import { AnomalyDashboard } from "./AnomalyDashboard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    input: (key: string, options?: { count?: number }) => {
      if (key === "dashboard:anomalies.durationSeconds" && options && "count" in options) {
        return `${String(options.count)}s`;
      }

      return key;
    },
  }),
}));

const Wrapper = ({ children }: PropsWithChildren) => <BaseWrapper>{children}</BaseWrapper>;

describe("AnomalyDashboard", () => {
  it("renders header, stat cards, and empty recent-anomalies table", () => {
    render(<AnomalyDashboard />, { wrapper: Wrapper });

    expect(screen.getByText("dashboard:anomalies.title")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.description")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.stats.last24h")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.stats.tasksMonitored")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.stats.algorithm")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(2);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.recent")).toBeInTheDocument();
    expect(screen.getByText("dashboard:anomalies.empty")).toBeInTheDocument();
  });
});
