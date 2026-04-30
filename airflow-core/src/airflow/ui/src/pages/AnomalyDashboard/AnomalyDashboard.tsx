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
import { Badge, Box, Flex, Heading, Table, Text, VStack } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { FiAlertTriangle } from "react-icons/fi";

// Placeholder type for anomaly records (replace with API types when backend is ready)
type AnomalyRecord = {
  dagId: string;
  detectedAt: string;
  durationSeconds: number;
  expectedRange: string;
  runId: string;
  taskId: string;
  type: "fast" | "slow";
};

// Placeholder data for the dashboard (replace with API call when ready)
const PLACEHOLDER_STATS = {
  algorithmsEnabled: "—",
  anomaliesLast24h: 0,
  tasksMonitored: 0,
};

const PLACEHOLDER_ANOMALIES: Array<AnomalyRecord> = [];

export const AnomalyDashboard = () => {
  const { t: translate } = useTranslation(["common", "dashboard"]);
  const stats = PLACEHOLDER_STATS;
  const anomalies = PLACEHOLDER_ANOMALIES;

  return (
    <Box overflow="auto" px={{ base: 2, md: 4 }}>
      <VStack alignItems="stretch" gap={6}>
        <Flex alignItems="center" gap={2}>
          <Box color="orange.500">
            <FiAlertTriangle size={28} />
          </Box>
          <Heading size="2xl">{translate("dashboard:anomalies.title")}</Heading>
        </Flex>

        <Text color="fg.muted" fontSize="sm">
          {translate("dashboard:anomalies.description")}
        </Text>

        <Flex flexWrap="wrap" gap={4}>
          <Box bg="bg.panel" borderRadius="lg" borderWidth="1px" minW="160px" px={4} py={3}>
            <Text color="fg.muted" fontSize="xs">
              {translate("dashboard:anomalies.stats.last24h")}
            </Text>
            <Heading size="lg">{stats.anomaliesLast24h}</Heading>
          </Box>
          <Box bg="bg.panel" borderRadius="lg" borderWidth="1px" minW="160px" px={4} py={3}>
            <Text color="fg.muted" fontSize="xs">
              {translate("dashboard:anomalies.stats.tasksMonitored")}
            </Text>
            <Heading size="lg">{stats.tasksMonitored}</Heading>
          </Box>
          <Box bg="bg.panel" borderRadius="lg" borderWidth="1px" minW="160px" px={4} py={3}>
            <Text color="fg.muted" fontSize="xs">
              {translate("dashboard:anomalies.stats.algorithm")}
            </Text>
            <Text fontWeight="medium">{stats.algorithmsEnabled}</Text>
          </Box>
        </Flex>

        <Box>
          <Heading mb={3} size="md">
            {translate("dashboard:anomalies.recent")}
          </Heading>
          <Table.Root size="sm" striped>
            <Table.Header bg="chakra-body-bg" position="sticky" top={0} zIndex={1}>
              <Table.Row>
                <Table.ColumnHeader>{translate("common:dagId")}</Table.ColumnHeader>
                <Table.ColumnHeader>{translate("common:task", { count: 1 })}</Table.ColumnHeader>
                <Table.ColumnHeader>{translate("common:runId")}</Table.ColumnHeader>
                <Table.ColumnHeader>{translate("dashboard:anomalies.columns.detected")}</Table.ColumnHeader>
                <Table.ColumnHeader>{translate("common:duration")}</Table.ColumnHeader>
                <Table.ColumnHeader>
                  {translate("dashboard:anomalies.columns.expectedRange")}
                </Table.ColumnHeader>
                <Table.ColumnHeader>{translate("dashboard:anomalies.columns.type")}</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {anomalies.length === 0 ? (
                <Table.Row>
                  <Table.Cell colSpan={7} py={8} textAlign="center">
                    <Text color="fg.muted">{translate("dashboard:anomalies.empty")}</Text>
                  </Table.Cell>
                </Table.Row>
              ) : (
                anomalies.map((anomalyRecord) => (
                  <Table.Row key={`${anomalyRecord.dagId}-${anomalyRecord.taskId}-${anomalyRecord.runId}`}>
                    <Table.Cell>{anomalyRecord.dagId}</Table.Cell>
                    <Table.Cell>{anomalyRecord.taskId}</Table.Cell>
                    <Table.Cell>{anomalyRecord.runId}</Table.Cell>
                    <Table.Cell>{anomalyRecord.detectedAt}</Table.Cell>
                    <Table.Cell>
                      {translate("dashboard:anomalies.durationSeconds", {
                        count: anomalyRecord.durationSeconds,
                      })}
                    </Table.Cell>
                    <Table.Cell>{anomalyRecord.expectedRange}</Table.Cell>
                    <Table.Cell>
                      <Badge colorPalette={anomalyRecord.type === "slow" ? "orange" : "blue"} size="sm">
                        {translate(`dashboard:anomalies.types.${anomalyRecord.type}`)}
                      </Badge>
                    </Table.Cell>
                  </Table.Row>
                ))
              )}
            </Table.Body>
          </Table.Root>
        </Box>
      </VStack>
    </Box>
  );
};
