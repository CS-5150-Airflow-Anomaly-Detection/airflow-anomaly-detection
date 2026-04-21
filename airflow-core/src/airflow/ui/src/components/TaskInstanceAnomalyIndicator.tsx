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
import { Badge, Box } from "@chakra-ui/react";
import { useTranslation } from "react-i18next";
import { FiAlertTriangle } from "react-icons/fi";
import { Link as RouterLink } from "react-router-dom";

import { BasicTooltip } from "src/components/BasicTooltip";

type Props = {
  readonly logsTo: string;
};

export const TaskInstanceAnomalyIndicator = ({ logsTo }: Props) => {
  const { t: translate } = useTranslation();

  return (
    <BasicTooltip
      content={translate("taskInstance.anomalyClickToSeeLogs", "Click to see logs")}
    >
      <RouterLink
        style={{
          display: "inline-flex",
          textDecoration: "none",
        }}
        to={logsTo}
      >
        <Badge
          alignItems="center"
          aria-label={translate("taskInstance.anomalyBadgeAria", "Anomaly")}
          as="span"
          borderRadius="full"
          colorPalette="red"
          cursor="pointer"
          data-testid="task-instance-anomaly-badge"
          display="inline-flex"
          flexShrink={0}
          fontSize="sm"
          gap={1}
          px={2}
          py={1}
          variant="solid"
        >
          <Box as="span" display="inline-flex" lineHeight={0}>
            <FiAlertTriangle size={14} strokeWidth={2.5} />
          </Box>
          {translate("taskInstance.anomalyBadge", "Anomaly")}
        </Badge>
      </RouterLink>
    </BasicTooltip>
  );
};
