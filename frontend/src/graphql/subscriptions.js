import { gql } from '@apollo/client';

export const ON_AGENT_STATUS_CHANGE = gql`
  subscription OnAgentStatusChange($agentId: ID) {
    onAgentStatusChange(agentId: $agentId) {
      agentId
      status
      lastActive
      message
    }
  }
`;

export const ON_NEW_MESSAGE = gql`
  subscription OnNewMessage {
    onNewMessage {
      id
      conversationId
      content
      sender
      timestamp
      agentId
      userId
    }
  }
`;

export const ON_COST_ANALYSIS_UPDATE = gql`
  subscription OnCostAnalysisUpdate {
    onCostAnalysisUpdate {
      id
      requestId
      status
      timeRange {
        startDate
        endDate
      }
      totalCost
      costByService {
        serviceName
        cost
        usageQuantity
        unit
      }
      costByTime {
        startTime
        endTime
        cost
      }
      anomalies {
        id
        serviceName
        amount
        percent
        reason
        detectedAt
      }
      createdAt
      updatedAt
    }
  }
`;

export const ON_NEW_OPTIMIZATION_RECOMMENDATION = gql`
  subscription OnNewOptimizationRecommendation {
    onNewOptimizationRecommendation {
      id
      title
      description
      resourceId
      resourceType
      estimatedSavings
      confidence
      difficulty
      status
      createdAt
    }
  }
`;
