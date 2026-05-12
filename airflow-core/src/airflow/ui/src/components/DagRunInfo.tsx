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
import { VStack, Text, Box, HStack } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { FiAlertTriangle } from "react-icons/fi";
import { Link as RouterLink } from "react-router-dom";

import type { DAGRunResponse } from "openapi/requests/types.gen";
import { StateBadge } from "src/components/StateBadge";
import Time from "src/components/Time";
import { Tooltip } from "src/components/ui";
import { getRelativeTime } from "src/utils/datetimeUtils";

type Props = {
  readonly anomalyUrl?: string;
  readonly endDate?: string | null;
  readonly isAnomalous?: boolean;
  readonly logicalDate?: string | null;
  readonly runAfter: string;
  readonly startDate?: string | null;
  readonly state?: DAGRunResponse["state"];
};

const hasValue = (value: string | null | undefined): value is string =>
  value !== undefined && value !== null && value !== "";

const DagRunInfo = ({ anomalyUrl, endDate, isAnomalous, logicalDate, runAfter, startDate, state }: Props) => {
  const { t: translate } = useTranslation("common");

  return (
    <Tooltip
      content={
        <VStack align="left" gap={0}>
          {state === undefined ? (
            <Text>
              {translate("dagDetails.nextRun")}: {getRelativeTime(runAfter)}
            </Text>
          ) : (
            <>
              <Text>
                {translate("state")}: {translate(`common:states.${state}`)}
              </Text>
              {hasValue(logicalDate) ? (
                <Text>
                  {translate("logicalDate")}: <Time datetime={logicalDate} showTooltip={false} />
                </Text>
              ) : undefined}
              {hasValue(startDate) ? (
                <Text>
                  {translate("startDate")}: <Time datetime={startDate} showTooltip={false} />
                </Text>
              ) : undefined}
              {hasValue(endDate) ? (
                <Text>
                  {translate("endDate")}: <Time datetime={endDate} showTooltip={false} />
                </Text>
              ) : undefined}
              {isAnomalous ? (
                <Text>{translate("anomalyDetected", "Performance anomaly detected")}</Text>
              ) : undefined}
            </>
          )}
        </VStack>
      }
    >
      <Box>
        <HStack display="inline-flex" gap={1}>
          <Time datetime={runAfter} mr={2} showTooltip={false} />
          {state !== undefined && <StateBadge aria-label={state} data-testid="state-badge" state={state} />}
          {state !== undefined && isAnomalous ? (
            <Box
              aria-label={translate("anomalyDetected", "Anomaly detected")}
              color="orange.600"
              flexShrink={0}
              lineHeight={0}
              onClick={
                anomalyUrl
                  ? (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                    }
                  : undefined
              }
            >
              {anomalyUrl ? (
                <RouterLink to={anomalyUrl}>
                  <FiAlertTriangle size={22} strokeWidth={2.75} />
                </RouterLink>
              ) : (
                <FiAlertTriangle size={22} strokeWidth={2.75} />
              )}
            </Box>
          ) : undefined}
        </HStack>
      </Box>
    </Tooltip>
  );
};

export default DagRunInfo;
