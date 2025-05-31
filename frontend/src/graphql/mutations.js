import { gql } from '@apollo/client';

export const SEND_MESSAGE = gql`
  mutation SendMessage($input: MessageInput!) {
    sendMessage(input: $input) {
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

export const REQUEST_COST_ANALYSIS = gql`
  mutation RequestCostAnalysis($input: CostAnalysisInput!) {
    requestCostAnalysis(input: $input) {
      id
      status
      timeRange {
        startDate
        endDate
      }
      granularity
      filters {
        dimension
        values
        operator
      }
      groupBy
      createdAt
    }
  }
`;

export const APPLY_OPTIMIZATION = gql`
  mutation ApplyOptimization($recommendationId: ID!) {
    applyOptimization(recommendationId: $recommendationId) {
      recommendationId
      status
      message
      timestamp
    }
  }
`;
