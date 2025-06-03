# FinOps Agent UI

A React-based frontend for the FinOps Agent Lambda function, built with AWS Amplify.

## Project Structure

```
finops-ui/
├── public/                 # Public assets
├── src/                    # Source code
│   ├── App.js              # Main application component
│   ├── App.css             # Application styles
│   ├── index.js            # Entry point
│   └── aws-exports.js      # AWS Amplify configuration (placeholder)
├── amplify.yml             # Amplify build configuration
├── package.json            # Dependencies and scripts
└── README.md               # This file
```

## Setup Instructions

### Prerequisites

- Node.js 14.x or later
- npm 6.x or later
- AWS account with appropriate permissions
- AWS CLI configured with your credentials

### Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### AWS Amplify Setup

1. Install the Amplify CLI:
   ```
   npm install -g @aws-amplify/cli
   ```

2. Configure Amplify:
   ```
   amplify configure
   ```

3. Initialize Amplify in the project:
   ```
   amplify init
   ```

4. Add authentication:
   ```
   amplify add auth
   ```

5. Add API for the Lambda function:
   ```
   amplify add api
   ```
   - Choose REST API
   - Configure the API to connect to your existing Lambda function

6. Update the configuration:
   ```
   amplify push
   ```

### Manual Deployment to AWS Amplify

1. Build the application:
   ```
   npm run build
   ```

2. Zip the build folder:
   ```
   cd build
   zip -r ../finops-ui-build.zip .
   ```

3. Upload the zip file to AWS Amplify Console:
   - Go to the [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
   - Choose "Deploy without Git provider"
   - Upload the zip file

## Integration with Lambda Function

The UI is designed to work with the FinOps Agent Lambda function. It sends queries to the Lambda function through API Gateway and displays the responses.

Before deploying, make sure to update the `aws-exports.js` file with your actual AWS resource IDs:

- `aws_cognito_identity_pool_id`: Your Cognito identity pool ID
- `aws_user_pools_id`: Your Cognito user pool ID
- `aws_user_pools_web_client_id`: Your Cognito user pool client ID
- `endpoint` in `aws_cloud_logic_custom`: Your API Gateway endpoint URL

## Customization

You can customize the UI by modifying the following files:

- `src/App.js`: Main application component
- `src/App.css`: Application styles
- `public/index.html`: HTML template

## License

This project is licensed under the MIT License.
