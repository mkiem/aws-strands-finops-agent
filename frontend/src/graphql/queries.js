import { gql } from '@apollo/client';

export const GET_AGENT_STATUS = gql`
  query GetAgentStatus($agentId: ID!) {
    getAgentStatus(agentId: $agentId) {
      agentId
      status
      lastActive
      message
    }
  }
`;

export const GET_COST_ANALYSIS = gql`
  query GetCostAnalysis($timeRange: TimeRangeInput!) {
    getCostAnalysis(timeRange: $timeRange) {
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

export const GET_OPTIMIZATION_RECOMMENDATIONS = gql`
  query GetOptimizationRecommendations {
    getOptimizationRecommendations {
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

export const GET_CONVERSATION_HISTORY = gql`
  query GetConversationHistory($limit: Int, $nextToken: String) {
    getConversationHistory(limit: $limit, nextToken: $nextToken) {
      items {
        id
        conversationId
        content
        sender
        timestamp
        agentId
        userId
      }
      nextToken
    }
  }
`;
