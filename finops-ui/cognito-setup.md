# Cognito Setup for FinOps Agent UI

This document provides instructions for setting up Amazon Cognito for user authentication in your FinOps Agent UI.

## Creating a Cognito User Pool

### Using AWS CLI

```bash
# Create a Cognito User Pool
aws cognito-idp create-user-pool \
  --pool-name "FinOpsStrands" \
  --auto-verify-attributes email \
  --schema '[{"Name":"email","Required":true,"Mutable":true}]' \
  --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}' \
  --username-attributes email

# Get the User Pool ID
USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 --query "UserPools[?Name=='FinOpsStrands'].Id" --output text)

# Create a User Pool Client
aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name "FinOpsStrands" \
  --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --supported-identity-providers COGNITO

# Get the User Pool Client ID
CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id $USER_POOL_ID --query "UserPoolClients[?ClientName=='FinOpsStrands'].ClientId" --output text)

# Create an Identity Pool
aws cognito-identity create-identity-pool \
  --identity-pool-name "FinOpsStrands" \
  --allow-unauthenticated-identities \
  --cognito-identity-providers ProviderName=cognito-idp.$AWS_REGION.amazonaws.com/us-east-1_DQpPM15TX,ClientId=5man7npqs0k2r3sbnu4sn82hpi,ServerSideTokenCheck=false

# Get the Identity Pool ID
IDENTITY_POOL_ID=$(aws cognito-identity list-identity-pools --max-results 60 --query "IdentityPools[?IdentityPoolName=='FinOpsStrands'].IdentityPoolId" --output text)

# Create IAM roles for authenticated and unauthenticated users
# (This is a simplified example - you should customize the policies based on your needs)

# Create authenticated role
aws iam create-role \
  --role-name FinOpsStrands_AuthRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "cognito-identity.amazonaws.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "cognito-identity.amazonaws.com:aud": "'$IDENTITY_POOL_ID'"
          },
          "ForAnyValue:StringLike": {
            "cognito-identity.amazonaws.com:amr": "authenticated"
          }
        }
      }
    ]
  }'

# Create unauthenticated role
aws iam create-role \
  --role-name FinOpsStrands_UnauthRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "cognito-identity.amazonaws.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "cognito-identity.amazonaws.com:aud": "'$IDENTITY_POOL_ID'"
          },
          "ForAnyValue:StringLike": {
            "cognito-identity.amazonaws.com:amr": "unauthenticated"
          }
        }
      }
    ]
  }'

# Attach policies to the roles
aws iam put-role-policy \
  --role-name FinOpsStrands_AuthRole \
  --policy-name CognitoAuthorizedPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "execute-api:Invoke"
        ],
        "Resource": "arn:aws:execute-api:'$AWS_REGION':'$ACCOUNT_ID':'$API_ID'/*/POST/query"
      }
    ]
  }'

aws iam put-role-policy \
  --role-name FinOpsStrands_UnauthRole \
  --policy-name CognitoUnauthorizedPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Deny",
        "Action": "*",
        "Resource": "*"
      }
    ]
  }'

# Set the roles for the identity pool
aws cognito-identity set-identity-pool-roles \
  --identity-pool-id $IDENTITY_POOL_ID \
  --roles authenticated=arn:aws:iam::${AWS_ACCOUNT_ID}:role/FinOpsStrands_AuthRole,unauthenticated=arn:aws:iam::${AWS_ACCOUNT_ID}:role/FinOpsStrands_UnauthRole
```

### Using AWS Console

1. Go to the [Amazon Cognito console](https://console.aws.amazon.com/cognito/home)
2. Click "Create user pool"
3. Configure sign-in experience:
   - Select "Email" as the Cognito user pool sign-in options
   - Click "Next"
4. Configure security requirements:
   - Set password policy as needed
   - Choose MFA enforcement (optional)
   - Click "Next"
5. Configure sign-up experience:
   - Select required attributes (email is recommended)
   - Click "Next"
6. Configure message delivery:
   - Choose "Send email with Cognito" for simplicity
   - Click "Next"
7. Integrate your app:
   - Enter "FinOpsAgentUserPool" as the User pool name
   - Enter "FinOpsAgentClient" as the App client name
   - Click "Next"
8. Review and create:
   - Review your settings
   - Click "Create user pool"
9. Create an identity pool:
   - Go to "Identity pools" in the Cognito console
   - Click "Create identity pool"
   - Enter "FinOpsAgentIdentityPool" as the Identity pool name
   - Enable "Guest access"
   - Configure Authentication providers:
     - Select "User Pool" as the provider
     - Select your user pool and client ID
   - Click "Create"
   - Create or select IAM roles for authenticated and unauthenticated users

## Creating a Test User

### Using AWS CLI

```bash
# Create a test user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --temporary-password "Temp123!" \
  --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true

# Set a permanent password for the test user
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --password "YourSecurePassword123!" \
  --permanent
```

### Using AWS Console

1. Go to the [Amazon Cognito console](https://console.aws.amazon.com/cognito/home)
2. Select your user pool
3. Go to "Users" in the left navigation
4. Click "Create user"
5. Enter the user information:
   - Email: admin@example.com
   - Check "Send an invitation to this new user?"
   - Check "Mark email as verified"
   - Set a temporary password
6. Click "Create user"

## Updating the React Application

Update the `aws-exports.js` file in your React application with the Cognito configuration:

```javascript
const awsmobile = {
    "aws_project_region": "us-east-1",
    "aws_cognito_identity_pool_id": "us-east-1:dd3fed4d-d712-440a-af16-b16bf5b9c2ef",
    "aws_cognito_region": "us-east-1",
    "aws_user_pools_id": "us-east-1_DQpPM15TX",
    "aws_user_pools_web_client_id": "kltti98jmcb93gm99p47qi85m",
    "oauth": {},
    "aws_cloud_logic_custom": [
        {
            "name": "finopsAgentAPI",
            "endpoint": "${API_GATEWAY_ENDPOINT}",
            "region": "us-east-1"
        }
    ]
};
```

Replace the placeholder values with your actual resource IDs.
