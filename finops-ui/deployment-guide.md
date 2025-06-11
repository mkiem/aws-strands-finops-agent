# FinOps Agent UI Deployment Guide

This comprehensive guide provides instructions for building, deploying, and maintaining the FinOps Agent UI on AWS Amplify.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Package Structure Requirements](#package-structure-requirements)
3. [Building and Packaging](#building-and-packaging)
4. [Deployment Process](#deployment-process)
5. [Authentication Setup](#authentication-setup)
6. [API Integration](#api-integration)
7. [Implementation Details](#implementation-details)
8. [Troubleshooting](#troubleshooting)
9. [Current Deployment Information](#current-deployment-information)
10. [Next Steps](#next-steps)

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with your credentials
- Node.js and npm installed
- Access to the FinOps Agent UI source code

## Package Structure Requirements

⚠️ **CRITICAL**: When deploying to AWS Amplify, all files MUST be at the root level of the zip file, NOT inside a subdirectory.

✅ **CORRECT Structure**:
```
finops-ui-build.zip
├── index.html
├── favicon.ico
├── asset-manifest.json
├── static/
│   ├── css/
│   └── js/
└── ...other files
```

❌ **INCORRECT Structure**:
```
finops-ui-build.zip
└── build/
    ├── index.html
    ├── favicon.ico
    ├── asset-manifest.json
    ├── static/
    │   ├── css/
    │   └── js/
    └── ...other files
```

## Building and Packaging

Follow these steps to create a properly structured deployment package:

```bash
# Navigate to the project directory
cd /home/ec2-user/projects/finopsAgent/finops-ui

# Build the application
npm run build

# Create a temporary directory for packaging
mkdir -p deployment-package

# Copy build contents to the temporary directory (NOT the build directory itself)
cp -r build/* deployment-package/

# Copy configuration files
cp src/aws-exports.js deployment-package/
cp src/config.js deployment-package/

# Create the zip file from the contents (not the directory)
cd deployment-package
zip -r ../finops-ui-build.zip .

# Upload to S3
cd ..
aws s3 cp finops-ui-build.zip s3://finops-deployment-packages-062025/finops-ui-build.zip

# Clean up
rm -rf deployment-package
```

## Deployment Process

### Option 1: Using AWS CLI

```bash
# Deploy to an existing Amplify app
aws amplify start-deployment \
  --app-id da7jmqelobr5a \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-build.zip
```

### Option 2: Creating a New Amplify App

```bash
# Create a new Amplify app
aws amplify create-app \
  --name "FinOpsAgentUI" \
  --description "FinOps Agent UI" \
  --platform WEB

# Get the app ID
APP_ID=$(aws amplify list-apps --query "apps[?name=='FinOpsAgentUI'].appId" --output text)

# Create a branch
aws amplify create-branch \
  --app-id $APP_ID \
  --branch-name staging

# Add custom routing rules for SPA
aws amplify update-app \
  --app-id $APP_ID \
  --custom-rules '[{"source": "/<*>", "target": "/index.html", "status": "404-200"}]'

# Create a deployment
aws amplify start-deployment \
  --app-id $APP_ID \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-build.zip
```

## Authentication Setup

### Cognito Configuration

1. **Use Existing User Pool**:
   - User Pool ID: `us-east-1_DQpPM15TX`
   - App Client ID: `4evk2m4ru8rrenij1ukg0044k6`
   - Identity Pool ID: `us-east-1:dd3fed4d-d712-440a-af16-b16bf5b9c2ef`

2. **Set Environment Variables**:
   ```bash
   aws amplify update-branch \
     --app-id da7jmqelobr5a \
     --branch-name staging \
     --environment-variables '{
       "REACT_APP_AWS_PROJECT_REGION": "us-east-1",
       "REACT_APP_AWS_COGNITO_IDENTITY_POOL_ID": "us-east-1:dd3fed4d-d712-440a-af16-b16bf5b9c2ef",
       "REACT_APP_AWS_COGNITO_REGION": "us-east-1",
       "REACT_APP_AWS_USER_POOLS_ID": "us-east-1_DQpPM15TX",
       "REACT_APP_AWS_USER_POOLS_WEB_CLIENT_ID": "4evk2m4ru8rrenij1ukg0044k6",
       "REACT_APP_API_ENDPOINT": "https://x015blgao0.execute-api.us-east-1.amazonaws.com/prod"
     }'
   ```

3. **Configuration Files**:
   - Create `aws-exports.js` and `config.js` with the appropriate Cognito settings
   - Include these files in the deployment package

### Test User

- Username: `testuser`
- Password: `SecurePassword123!`

## API Integration

The UI integrates with the FinOps Agent Lambda function through API Gateway:

- **API Endpoint**: `https://71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod/query`
- **Method**: POST
- **Request Format**:
  ```json
  {
    "query": "What is my current AWS spend?"
  }
  ```
- **Response Format**:
  ```json
  {
    "query": "What is my current AWS spend?",
    "response": [
      { "text": "# AWS Cost Summary\n\n" },
      { "text": "## Total Cost: $123.45 USD\n\n" },
      ...
    ]
  }
  ```

## Implementation Details

### Key Components

1. **App.js**:
   - Main application component
   - Handles authentication with Cognito
   - Manages API requests and responses
   - Stores response data in state

2. **FinOpsResponse.jsx**:
   - Renders structured responses from the Lambda function
   - Extracts and displays cost information in a summary card
   - Uses ReactMarkdown to render formatted content
   - Handles different response formats

3. **Response Processing**:
   ```jsx
   // Extract and combine markdown content from array format
   const markdownContent = Array.isArray(response) 
     ? response.map(chunk => chunk.text || '').join('') 
     : response;
   
   // Render with ReactMarkdown
   <ReactMarkdown>{markdownContent}</ReactMarkdown>
   ```

## Troubleshooting

### Common Issues and Solutions

1. **404 Errors**:
   - Ensure your package structure is correct (files at root level)
   - Verify custom routing rules are set correctly
   - Check if CloudFront distribution is properly configured

2. **Authentication Issues**:
   - Verify Cognito configuration in environment variables
   - Check that aws-exports.js and config.js are included in the deployment
   - Try creating a new app client in the same user pool

3. **Response Formatting Issues**:
   - Check browser console for JavaScript errors
   - Verify that ReactMarkdown is properly handling the response format
   - Ensure the Lambda function is returning the expected response structure

## Current Deployment Information

- **Amplify App ID**: `da7jmqelobr5a`
- **App Name**: AWS Fin Ops
- **Branch**: staging
- **Deployment URL**: [https://staging.da7jmqelobr5a.amplifyapp.com](https://staging.da7jmqelobr5a.amplifyapp.com)
- **Deployment Status**: SUCCEED
- **Last Deployment**: June 10, 2025

## Next Steps

1. **Monitoring and Maintenance**:
   - Monitor usage and performance
   - Collect user feedback
   - Update components as needed

2. **Feature Enhancements**:
   - Add charts and graphs for cost visualization
   - Implement more interactive elements
   - Support additional query types and response formats

3. **Production Readiness**:
   - Set up a custom domain
   - Implement CI/CD with a Git provider
   - Add analytics for usage tracking
