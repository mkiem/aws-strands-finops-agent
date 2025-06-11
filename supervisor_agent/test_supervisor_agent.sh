#!/bin/bash

# Test script for AWS FinOps Supervisor Agent
# Run this after the supervisor agent is successfully deployed

echo "Testing AWS FinOps Supervisor Agent..."

# Test 1: Simple query
echo "=== Test 1: Simple Query ==="
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"query": "What are my current AWS costs and optimization opportunities?"}' \
  --region us-east-1 \
  response1.json

echo "Response:"
cat response1.json | jq .
echo ""

# Test 2: Cost analysis query
echo "=== Test 2: Cost Analysis Query ==="
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"query": "Provide detailed cost analysis for this month"}' \
  --region us-east-1 \
  response2.json

echo "Response:"
cat response2.json | jq .
echo ""

# Test 3: Optimization query
echo "=== Test 3: Optimization Query ==="
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"query": "What cost optimization recommendations do you have?"}' \
  --region us-east-1 \
  response3.json

echo "Response:"
cat response3.json | jq .
echo ""

# Test 4: API Gateway format
echo "=== Test 4: API Gateway Format ==="
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"body": "{\"query\": \"What are my AWS costs for June 2025?\"}"}' \
  --region us-east-1 \
  response4.json

echo "Response:"
cat response4.json | jq .
echo ""

# Test 5: Alternative input format
echo "=== Test 5: Alternative Input Format ==="
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"inputText": "Show me cost optimization recommendations"}' \
  --region us-east-1 \
  response5.json

echo "Response:"
cat response5.json | jq .
echo ""

# Clean up response files
rm -f response*.json

echo "Testing complete!"
