# FinOps Agent UI Deployment Instructions

This document provides instructions for deploying the FinOps Agent UI to AWS Amplify.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured with your credentials
- The `finops-ui-build.zip` file created from the build process

## CRITICAL: Package Structure Requirements

⚠️ **IMPORTANT**: When deploying to AWS Amplify, all files MUST be at the root level of the zip file, NOT inside a subdirectory.

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

## Creating the Deployment Package

Follow these steps to create a properly structured deployment package:

```bash
# Navigate to the project directory
cd /path/to/finops-ui

# Build the application
npm run build

# Create a temporary directory for packaging
mkdir -p deployment-package

# Copy build contents to the temporary directory (NOT the build directory itself)
cp -r build/* deployment-package/

# Create the zip file from the contents (not the directory)
cd deployment-package
zip -r ../finops-ui-build.zip .

# Upload to S3
cd ..
aws s3 cp finops-ui-build.zip s3://finops-deployment-packages-062025/finops-ui-build.zip

# Clean up
rm -rf deployment-package
```

## Deployment Options

### Option 1: Manual Deployment via AWS Amplify Console

1. Go to the [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
2. Click "New app" > "Host web app"
3. Select "Deploy without Git provider" and click "Continue"
4. Enter "FinOps Agent UI" as the App name
5. Drag and drop the `finops-ui-build.zip` file or click to upload it
6. Click "Save and deploy"

### Option 2: Deployment via AWS CLI

```bash
# Create an Amplify app
aws amplify create-app \
  --name "FinOpsAgentUI" \
  --description "FinOps Agent UI" \
  --platform WEB

# Get the app ID
APP_ID=$(aws amplify list-apps --query "apps[?name=='FinOpsAgentUI'].appId" --output text)

# Create a branch
aws amplify create-branch \
  --app-id $APP_ID \
  --branch-name main

# Add custom routing rules for SPA
aws amplify update-app \
  --app-id $APP_ID \
  --custom-rules '[{"source": "/<*>", "target": "/index.html", "status": "404-200"}]'

# Create a deployment
aws amplify start-deployment \
  --app-id $APP_ID \
  --branch-name main \
  --source-url s3://finops-deployment-packages-062025/finops-ui-build.zip
```

## Setting Up Authentication

After deploying the UI, you need to set up authentication with Amazon Cognito:

1. Create a Cognito User Pool and Identity Pool as described in `cognito-setup.md`
2. Update the environment variables in the Amplify Console:
   - Go to the [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
   - Select your app
   - Go to "Environment variables" in the left navigation
   - Add the following environment variables:
     - `REACT_APP_USER_POOL_ID`: Your Cognito User Pool ID
     - `REACT_APP_USER_POOL_WEB_CLIENT_ID`: Your Cognito User Pool Client ID
     - `REACT_APP_IDENTITY_POOL_ID`: Your Cognito Identity Pool ID
     - `REACT_APP_API_ENDPOINT`: Your API Gateway endpoint URL
   - Click "Save"
3. Redeploy the application

## Setting Up API Gateway

Follow the instructions in `api-gateway-setup.md` to set up an API Gateway endpoint for your Lambda function.

## Testing the Deployment

1. Go to the URL provided by AWS Amplify after deployment
2. You should see the FinOps Agent UI login screen
3. Sign in with a user created in your Cognito User Pool
4. After signing in, you should see the FinOps Agent dashboard
5. Enter a query and click "Ask" to test the integration with your Lambda function

## Troubleshooting

If you encounter issues with the deployment:

1. **404 Errors**: Ensure your package structure is correct (files at root level) and custom routing rules are set
2. **CloudFront Issues**: Check if CloudFront distributions are created properly
3. **Build Errors**: Check the Amplify build logs for errors
4. **Environment Variables**: Verify that environment variables are set correctly
5. **API Integration**: Check the browser console for JavaScript errors
6. **Backend Issues**: Verify that the API Gateway endpoint is configured correctly
7. **Lambda Errors**: Check the Lambda function logs for errors

## Next Steps

1. Set up a custom domain for your application
2. Configure CI/CD with a Git provider
3. Add analytics to track usage
4. Implement additional features such as:
   - Cost visualization
   - Scheduled reports
   - User management
   - Customizable dashboards
