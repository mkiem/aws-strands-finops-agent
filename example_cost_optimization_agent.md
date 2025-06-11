CostOptimizationAgentAlias:
    Type: AWS::Bedrock::AgentAlias
    Properties:
      AgentId: !Ref CostOptimizationAgent
      AgentAliasName: "CostOptimization"
      Description: "Agent to get Trusted Advisor Check information for cost optimization pillar."      

  CostOptimizationAgent:
    Type: AWS::Bedrock::Agent
    Properties:
      AgentName: CostOptimizationAgent
      Description: You are an AI Agent which will get Cost Optimization Data.
      Instruction: |
        "You are a Cost Analysis Agent specializing in AWS Trusted Advisor's Cost Optimization findings.
        YOUR CORE FUNCTION: You directly access AWS Trusted Advisor data to identify cost-saving opportunities in AWS accounts, focusing exclusively on cost optimization recommendations.
       
        YOUR RESPONSIBILITIES:
        Pull real-time data from AWS Trusted Advisor
        Show exact dollar amounts to 2 decimal places
        Present findings exactly as retrieved
        Format all costs in USD ($XX.XX)
        Display potential savings without calculations
        
        YOU ANALYZE:
        Underutilized resources
        Idle or unused resources
        Reserved Instance opportunities
        Over provisioned resources
        Service usage patterns
        
        YOU WILL NEVER:
        Perform calculations yourself
        Round numbers or estimate savings
        Make assumptions about costs
        Use the Calculator Agent
        Provide non-cost recommendations
        
        DATA PRESENTATION:
        Each finding includes:
        Check name
        Current status
        Number of affected resources
        Exact monthly savings potential
        Optimization description
        
        SAMPLE QUESTIONS YOU HANDLE:
        - What are my current cost saving opportunities?
        - Show me underutilized EC2 instances
        - What's my total potential monthly savings?
        - Which resources need cost optimization?
        - List all idle resources I can remove
        - Give me current cost optimization recommendations
        
        RESPONSE FORMAT:
          - Potential Monthly Savings: $XXX.XX
          - Top Recommendations:
          
          [Check Name]
          Status: [Current Status]
          Resources Affected: [Number]
          Monthly Savings: $XXX.XX
          Action: [Brief Description]
          
          LIMITATIONS:
          Show only cost optimization checks
          Present data exactly as received
          Focus on actionable recommendations
          Exclude security and performance findings
          No manual calculations or estimates
          
          ERROR HANDLING:
          You will clearly state when:
          Data is unavailable
          Requests are outside scope
          API limits are reached
          Access is restricted
          
          Remember: You provide only actual AWS Trusted Advisor cost optimization data, never calculated or estimated values."
      AutoPrepare: true
      AgentResourceRoleArn: !GetAtt BedrockAgentExecutionRole.Arn
      IdleSessionTTLInSeconds: 1800
      FoundationModel: !Ref SubAgentFoundationModel
      ActionGroups:
        - ActionGroupName: TrustedAdvisorListRecommendationResources
          Description: Gets List of resources from TA
          ActionGroupExecutor: 
            Lambda: !GetAtt TrustedAdvisorListRecommendationResources.Arn
          FunctionSchema:
            Functions: 
              - Description: This function will help you to get the list of resources associated with a recommendation identifier.
                Name: get_list
                Parameters: 
                  recommendationIdentifier:
                    Description: The recommendationIdentifier value provided by the trusted advisor tool for each. The user don't manage this id, you should get it first
                    Required: True
                    Type: string
                RequireConfirmation: DISABLED
        - ActionGroupName: TrustedAdvisorListRecommendations
          Description: Gets data from TA
          ActionGroupExecutor: 
            Lambda: !GetAtt TrustedAdvisorListRecommendations.Arn                
          FunctionSchema:
            Functions: 
              - Description: This function will return all the cost optimization available to address.
                Name: RecommendationCommand
                RequireConfirmation: DISABLED

  CostAnalysisAgentAlias:
    Type: AWS::Bedrock::AgentAlias
    Properties:
      AgentId: !Ref CostAnalysisAgent
      AgentAliasName: "CostAnalysis"
      Description: "Agent to get Cost and Forecast"      

  CostAnalysisAgent:
    Type: AWS::Bedrock::Agent
    Properties:
      AgentName: CostAnalysisAgent
      Description: You are an AI Agent which will get Cost Usage and Forecast for a given time period.
      Instruction: |
        "You can help to analyze your AWS costs. Here's what you can do:
        1. Call the ClockandCalendarActionGroup tool for any date calculation first   (Current year, last year, last month, last 5 months, Q1, Quarter 2, last 10 days etc)
          - First get the current date and then calculate the start and end date by interpreting users question.
        2. Get the start and end date and call the CostForecastActionGroup tool for any cost forecast or estimate or prediction for future end date
        3. Get the start and end date and call the CostAnalysisActionGroup tool for any current or historical end date
        4. Call the CostSavingsPlanActionGroup for any savings plan user questions
        5. NEVER allow the model to do any calculation EVER, use the results from the tool only.  If you don't have it then mention that in your response, NEVER generate anything on your own in regards to calculation
        6. NEVER display your plan in your output when you send the final response
        7. The data you are providing is cost sensitive so NEVER reply from your memory. For Every question follow the process to call the ClockandCalendarActionGroup tool first and then CostAnalysisActionGroup or CostForecastActionGroup Tool analyzing the question. Strictly NEVER answer from your memory.
        8. Group By specific cost. Group by can be Service, usage type, linked accounts, region, billing entity depending upon the question asked by the user. Default group by will be Service
        9. Specific service cost. Get the service name from question and pass it to the CostAnalysisActionGroup or CostForecastActionGroup Tool analyzing the question. Do not change or update the service name. Send it as it is to the CostAnalysisActionGroup or CostForecastActionGroup
        10. If you receive You haven't enabled historical data beyond 14 months., return the answer as it is without any changes.
        11. for cost forecast/projection/estimate request, use the requested_period_forecast to get the forecasted amount. 

        DO NOT:
        - Calculate sums, averages, or any mathematical operations
        - Estimate or approximate numbers
        - Convert between units or currencies
        - Perform date calculations

        DO:
        - Use only numbers returned by the Lambda function
        - Respond 'This calculation is not supported' for unsupported operations
        - Format and present numbers from the API response
        - Explain data without modifying values

        For each query, you should ALWAYS follow the below format in HTML:
        - The total cost for the period
        - Time periods (start and end dates). always provide the start and end date in the output from period
        - Details of top 10 group by (Group By can be service, usage type, accounts depending on the user question)
        - All costs in USD
        - Add emojis in your respones and try to output in a nice format depending if the items is a list or a pragraph

        Important Note: Think step-by-step.  First, think through .... Then think through ... Finally, answer ...

        To get started, you can ask questions like:
        - What were my AWS costs for January 2025?
        - Show me my AWS costs between March 2024 and December 2024
        - What's my current AWS spending?
        - What were my top expenses last month?
        - Show me the costs for Q1 2024
        - What were my highest costs in 2024?
        - What is my cost forecast for Nov 2025?
        - You can specify dates in various formats: YYYY-MM-DD
        - Specific months: 'January 2025'
        - Date ranges: '2024-01-01 to 2024-12-31'
        - Quarters: 'Q1 2024'
        - Years: '2024'
        - Relative periods: 'last month', 'current year'"

      AutoPrepare: true
      AgentResourceRoleArn: !GetAtt BedrockAgentExecutionRole.Arn
      IdleSessionTTLInSeconds: 1800
      FoundationModel: !Ref SubAgentFoundationModel
      ActionGroups:
        - ActionGroupName: ClockandCalendarActionGroup
          Description: This action group will get today date by calling lambda function
          ActionGroupExecutor: 
            Lambda: !GetAtt ClockandCalendar.Arn
          FunctionSchema:
            Functions: 
              - Description: If the user provides a city or country to be considered as a time zone, then you should pass the timezone for that location. For example UTC, PST, CST, America/Chicago.
                Name: GetDateAndTime
                Parameters: 
                  timezone:
                    Description: If the user provides a city or country to be considered as a time zone, then you should pass the timezone for that location. For example UTC, PST, CST, America/Chicago.
                    Required: False
                    Type: string
                RequireConfirmation: DISABLED
        - ActionGroupName: CostAnalysisActionGroup
          Description: Gets details from AWS Cost Explorer
          ActionGroupExecutor: 
            Lambda: !GetAtt CostAnalysis.Arn
          ApiSchema: 
            Payload: |
              {
                  "openapi": "3.0.0",
                  "info": {
                      "title": "AWS Cost Explorer API",
                      "description": "API for retrieving AWS cost and usage data",
                      "version": "1.0.0"
                  },
                  "paths": {
                      "/get_cost_and_usage": {
                          "post": {
                              "summary": "Get general AWS cost and usage data",
                              "description": "Retrieves cost and usage data grouped by service, account, region, or usage type",
                              "operationId": "getCostAndUsage",
                              "parameters": [
                                  {
                                      "name": "start_date",
                                      "in": "query",
                                      "description": "Start date for cost analysis (YYYY-MM-DD)",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "format": "date"
                                      }
                                  },
                                  {
                                      "name": "end_date",
                                      "in": "query",
                                      "description": "End date for cost analysis (YYYY-MM-DD)",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "format": "date"
                                      }
                                  },
                                  {
                                      "name": "group_by",
                                      "in": "query",
                                      "description": "How to group the cost data",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "enum": [
                                              "SERVICE",
                                              "USAGE_TYPE",
                                              "LINKED_ACCOUNT",
                                              "REGION",
                                              "BILLING_ENTITY"
                                          ],
                                          "default": "SERVICE"
                                      }
                                  },
                                  {
                                      "name": "granularity",
                                      "in": "query",
                                      "description": "Time granularity of the results",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "enum": [
                                              "DAILY",
                                              "MONTHLY",
                                              "YEARLY"
                                          ],
                                          "default": "MONTHLY"
                                      }
                                  }
                              ],
                              "responses": {
                                  "200": {
                                      "description": "Successful operation",
                                      "content": {
                                          "application/json": {
                                              "schema": {
                                                  "type": "object",
                                                  "properties": {
                                                      "messageVersion": {
                                                          "type": "string"
                                                      },
                                                      "response": {
                                                          "type": "object",
                                                          "properties": {
                                                              "body": {
                                                                  "type": "object",
                                                                  "properties": {
                                                                      "message": {
                                                                          "type": "string"
                                                                      },
                                                                      "granularity": {
                                                                          "type": "string"
                                                                      },
                                                                      "period_total": {
                                                                          "type": "object",
                                                                          "properties": {
                                                                              "amount": {
                                                                                  "type": "string"
                                                                              },
                                                                              "unit": {
                                                                                  "type": "string"
                                                                              }
                                                                          }
                                                                      },
                                                                      "period": {
                                                                          "type": "object",
                                                                          "properties": {
                                                                              "start": {
                                                                                  "type": "string"
                                                                              },
                                                                              "end": {
                                                                                  "type": "string"
                                                                              }
                                                                          }
                                                                      },
                                                                      "top_10_services": {
                                                                          "type": "array",
                                                                          "items": {
                                                                              "type": "object",
                                                                              "properties": {
                                                                                  "name": {
                                                                                      "type": "string"
                                                                                  },
                                                                                  "amount": {
                                                                                      "type": "string"
                                                                                  },
                                                                                  "unit": {
                                                                                      "type": "string"
                                                                                  }
                                                                              }
                                                                          }
                                                                      },
                                                                      "data": {
                                                                          "type": "array",
                                                                          "items": {
                                                                              "type": "object",
                                                                              "properties": {
                                                                                  "time_period": {
                                                                                      "type": "object",
                                                                                      "properties": {
                                                                                          "start": {
                                                                                              "type": "string"
                                                                                          },
                                                                                          "end": {
                                                                                              "type": "string"
                                                                                          }
                                                                                      }
                                                                                  },
                                                                                  "total_cost": {
                                                                                      "type": "object",
                                                                                      "properties": {
                                                                                          "amount": {
                                                                                              "type": "string"
                                                                                          },
                                                                                          "unit": {
                                                                                              "type": "string"
                                                                                          }
                                                                                      }
                                                                                  },
                                                                                  "group_by": {
                                                                                      "type": "string"
                                                                                  },
                                                                                  "items": {
                                                                                      "type": "array",
                                                                                      "items": {
                                                                                          "type": "object",
                                                                                          "properties": {
                                                                                              "name": {
                                                                                                  "type": "string"
                                                                                              },
                                                                                              "amount": {
                                                                                                  "type": "string"
                                                                                              },
                                                                                              "unit": {
                                                                                                  "type": "string"
                                                                                              }
                                                                                          }
                                                                                      }
                                                                                  }
                                                                              }
                                                                          }
                                                                      }
                                                                  }
                                                              }
                                                          }
                                                      }
                                                  }
                                              }
                                          }
                                      }
                                  }
                              }
                          }
                      },
                      "/get_service_costs": {
                          "post": {
                              "summary": "Get costs for specific AWS services",
                              "description": "Retrieves cost data for specified AWS services",
                              "operationId": "getServiceCosts",
                              "parameters": [
                                  {
                                      "name": "services",
                                      "in": "query",
                                      "description": "Comma-separated list of AWS services",
                                      "required": true,
                                      "schema": {
                                          "type": "string"
                                      }
                                  },
                                  {
                                      "name": "start_date",
                                      "in": "query",
                                      "description": "Start date for cost analysis (YYYY-MM-DD)",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "format": "date"
                                      }
                                  },
                                  {
                                      "name": "end_date",
                                      "in": "query",
                                      "description": "End date for cost analysis (YYYY-MM-DD)",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "format": "date"
                                      }
                                  },
                                  {
                                      "name": "granularity",
                                      "in": "query",
                                      "description": "Time granularity of the results",
                                      "required": false,
                                      "schema": {
                                          "type": "string",
                                          "enum": [
                                              "DAILY",
                                              "MONTHLY",
                                              "YEARLY"
                                          ],
                                          "default": "MONTHLY"
                                      }
                                  }
                              ],
                              "responses": {
                                  "200": {
                                      "description": "Successful operation",
                                      "content": {
                                          "application/json": {
                                              "schema": {
                                                  "type": "object",
                                                  "properties": {
                                                      "messageVersion": {
                                                          "type": "string"
                                                      },
                                                      "response": {
                                                          "type": "object",
                                                          "properties": {
                                                              "body": {
                                                                  "type": "object",
                                                                  "properties": {
                                                                      "message": {
                                                                          "type": "string"
                                                                      },
                                                                      "period": {
                                                                          "type": "object",
                                                                          "properties": {
                                                                              "start": {
                                                                                  "type": "string"
                                                                              },
                                                                              "end": {
                                                                                  "type": "string"
                                                                              }
                                                                          }
                                                                      },
                                                                      "total_cost": {
                                                                          "type": "object",
                                                                          "properties": {
                                                                              "amount": {
                                                                                  "type": "string"
                                                                              },
                                                                              "unit": {
                                                                                  "type": "string"
                                                                              }
                                                                          }
                                                                      },
                                                                      "service_totals": {
                                                                          "type": "array",
                                                                          "items": {
                                                                              "type": "object",
                                                                              "properties": {
                                                                                  "service": {
                                                                                      "type": "string"
                                                                                  },
                                                                                  "total_cost": {
                                                                                      "type": "object",
                                                                                      "properties": {
                                                                                          "amount": {
                                                                                              "type": "string"
                                                                                          },
                                                                                          "unit": {
                                                                                              "type": "string"
                                                                                          }
                                                                                      }
                                                                                  }
                                                                              }
                                                                          }
                                                                      },
                                                                      "monthly_breakdown": {
                                                                          "type": "array",
                                                                          "items": {
                                                                              "type": "object",
                                                                              "properties": {
                                                                                  "time_period": {
                                                                                      "type": "object",
                                                                                      "properties": {
                                                                                          "start": {
                                                                                              "type": "string"
                                                                                          },
                                                                                          "end": {
                                                                                              "type": "string"
                                                                                          }
                                                                                      }
                                                                                  },
                                                                                  "total_cost": {
                                                                                      "type": "object",
                                                                                      "properties": {
                                                                                          "amount": {
                                                                                              "type": "string"
                                                                                          },
                                                                                          "unit": {
                                                                                              "type": "string"
                                                                                          }
                                                                                      }
                                                                                  },
                                                                                  "group_by": {
                                                                                      "type": "string"
                                                                                  },
                                                                                  "items": {
                                                                                      "type": "array",
                                                                                      "items": {
                                                                                          "type": "object",
                                                                                          "properties": {
                                                                                              "name": {
                                                                                                  "type": "string"
                                                                                              },
                                                                                              "amount": {
                                                                                                  "type": "string"
                                                                                              },
                                                                                              "unit": {
                                                                                                  "type": "string"
                                                                                              }
                                                                                          }
                                                                                      }
                                                                                  }
                                                                              }
                                                                          }
                                                                      }
                                                                  }
                                                              }
                                                          }
                                                      }
                                                  }
                                              }
                                          }
                                      }
                                  },
                                  "400": {
                                      "description": "Bad request",
                                      "content": {
                                          "application/json": {
                                              "schema": {
                                                  "type": "object",
                                                  "properties": {
                                                      "message": {
                                                          "type": "string"
                                                      }
                                                  }
                                              }
                                          }
                                      }
                                  },
                                  "500": {
                                      "description": "Internal server error",
                                      "content": {
                                          "application/json": {
                                              "schema": {
                                                  "type": "object",
                                                  "properties": {
                                                      "message": {
                                                          "type": "string"
                                                      }
                                                  }
                                              }
                                          }
                                      }
                                  }
                              }
                          }
                      }
                  },
                  "components": {
                      "schemas": {
                          "Error": {
                              "type": "object",
                              "properties": {
                                  "message": {
                                      "type": "string"
                                  }
                              }
                          }
                      }
                  }
              }