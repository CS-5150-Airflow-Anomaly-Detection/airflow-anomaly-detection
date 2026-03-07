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
import { useParams } from "react-router-dom";

// Placeholder type (replace with API types when backend is ready)
type AnomalyRecord = {
  taskId: string;
  runId: string;
  detectedAt: string;
  durationSeconds: number;
  expectedRange: string;
  type: "slow" | "fast";
};

const PLACEHOLDER_ANOMALIES: AnomalyRecord[] = [];

export const Anomalies = () => {
  const { dagId = "" } = useParams();
  const anomalies = PLACEHOLDER_ANOMALIES;

  return (
    <Box overflow="auto" px={{ base: 2, md: 4 }}>
      <VStack alignItems="stretch" gap={6}>
        <Flex alignItems="center" gap={2}>
          <Box color="orange.500">
            <FiAlertTriangle size={24} />
          </Box>
          <Heading size="lg">Task performance anomalies</Heading>
        </Flex>

        <Text color="fg.muted" fontSize="sm">
          Tasks in this DAG that ran significantly faster or slower than their historical 
          baselines are listed below. 
          Use this to spot performance regressions or unexpected speedups.
        </Text>

        <Box>
          <Heading mb={3} size="sm">
            Recent anomalies
          </Heading>
          <Table.Root size="sm" striped>
            <Table.Header bg="chakra-body-bg" position="sticky" top={0} zIndex={1}>
              <Table.Row>
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
                  <Table.Cell colSpan={6} py={8} textAlign="center">
                    <Text color="fg.muted">
                      No performance anomalies in recent runs.
                    </Text>
                  </Table.Cell>
                </Table.Row>
              ) : (
                anomalies.map((a) => (
                  <Table.Row key={`${a.taskId}-${a.runId}`}>
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
