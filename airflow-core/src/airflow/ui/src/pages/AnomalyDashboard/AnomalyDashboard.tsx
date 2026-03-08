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
  Table,
  Text,
  VStack,
} from "@chakra-ui/react";
import { FiAlertTriangle } from "react-icons/fi";

// Placeholder type for anomaly records (replace with API types when backend is ready)
type AnomalyRecord = {
  dagId: string;
  taskId: string;
  runId: string;
  detectedAt: string;
  durationSeconds: number;
  expectedRange: string;
  type: "slow" | "fast";
};

// Placeholder data for the dashboard (replace with API call when ready)
const PLACEHOLDER_STATS = {
  anomaliesLast24h: 0,
  tasksMonitored: 0,
  algorithmsEnabled: "—",
};

const PLACEHOLDER_ANOMALIES: AnomalyRecord[] = [];

export const AnomalyDashboard = () => {
  const stats = PLACEHOLDER_STATS;
  const anomalies = PLACEHOLDER_ANOMALIES;

  return (
    <Box overflow="auto" px={{ base: 2, md: 4 }}>
      <VStack alignItems="stretch" gap={6}>
        <Flex alignItems="center" gap={2}>
          <Box color="orange.500">
            <FiAlertTriangle size={28} />
          </Box>
          <Heading size="2xl">Task Performance Anomalies</Heading>
        </Flex>

        <Text color="fg.muted" fontSize="sm">
          Detect tasks that ran significantly faster or slower than their
          historical baseline. Data will appear here once the anomaly
          detection backend is connected.
        </Text>

        <Flex flexWrap="wrap" gap={4}>
          <Box
            bg="bg.panel"
            borderRadius="lg"
            borderWidth="1px"
            minW="160px"
            px={4}
            py={3}
          >
            <Text color="fg.muted" fontSize="xs">
              Anomalies (last 24h)
            </Text>
            <Heading size="lg">{stats.anomaliesLast24h}</Heading>
          </Box>
          <Box
            bg="bg.panel"
            borderRadius="lg"
            borderWidth="1px"
            minW="160px"
            px={4}
            py={3}
          >
            <Text color="fg.muted" fontSize="xs">
              Tasks monitored
            </Text>
            <Heading size="lg">{stats.tasksMonitored}</Heading>
          </Box>
          <Box
            bg="bg.panel"
            borderRadius="lg"
            borderWidth="1px"
            minW="160px"
            px={4}
            py={3}
          >
            <Text color="fg.muted" fontSize="xs">
              Detection algorithm
            </Text>
            <Text fontWeight="medium">{stats.algorithmsEnabled}</Text>
          </Box>
        </Flex>

        <Box>
          <Heading mb={3} size="md">
            Recent anomalies
          </Heading>
          <Table.Root size="sm" striped>
            <Table.Header bg="chakra-body-bg" position="sticky" top={0} zIndex={1}>
              <Table.Row>
                <Table.ColumnHeader>DAG</Table.ColumnHeader>
                <Table.ColumnHeader>Task</Table.ColumnHeader>
                <Table.ColumnHeader>Run</Table.ColumnHeader>
                <Table.ColumnHeader>Detected</Table.ColumnHeader>
                <Table.ColumnHeader>Duration</Table.ColumnHeader>
                <Table.ColumnHeader>Expected range</Table.ColumnHeader>
                <Table.ColumnHeader>Type</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {anomalies.length === 0 ? (
                <Table.Row>
                  <Table.Cell colSpan={7} py={8} textAlign="center">
                    <Text color="fg.muted">
                      No anomalies detected yet. Run DAGs and enable anomaly
                      detection to see results here.
                    </Text>
                  </Table.Cell>
                </Table.Row>
              ) : (
                anomalies.map((a) => (
                  <Table.Row key={`${a.dagId}-${a.taskId}-${a.runId}`}>
                    <Table.Cell>{a.dagId}</Table.Cell>
                    <Table.Cell>{a.taskId}</Table.Cell>
                    <Table.Cell>{a.runId}</Table.Cell>
                    <Table.Cell>{a.detectedAt}</Table.Cell>
                    <Table.Cell>{a.durationSeconds}s</Table.Cell>
                    <Table.Cell>{a.expectedRange}</Table.Cell>
                    <Table.Cell>
                      <Badge
                        colorPalette={a.type === "slow" ? "orange" : "blue"}
                        size="sm"
                      >
                        {a.type}
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
