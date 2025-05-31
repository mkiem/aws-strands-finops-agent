import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { getMainDefinition } from '@apollo/client/utilities';
import { createAuthLink } from 'aws-appsync-auth-link';
import { createSubscriptionHandshakeLink } from 'aws-appsync-subscription-link';
import { Auth } from 'aws-amplify';

// Get AppSync configuration from environment variables or config file
const appSyncConfig = {
  url: process.env.REACT_APP_APPSYNC_URL,
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  auth: {
    type: 'AMAZON_COGNITO_USER_POOLS',
    jwtToken: async () => (await Auth.currentSession()).getIdToken().getJwtToken(),
  },
};

// Create HTTP link for queries and mutations
const httpLink = createHttpLink({
  uri: appSyncConfig.url,
});

// Create auth link for authentication
const authLink = setContext(async (_, { headers }) => {
  try {
    const session = await Auth.currentSession();
    const token = session.getIdToken().getJwtToken();
    
    return {
      headers: {
        ...headers,
        Authorization: token,
      },
    };
  } catch (error) {
    console.error('Error getting authentication token:', error);
    return { headers };
  }
});

// Create AppSync auth link
const appsyncAuthLink = createAuthLink({
  url: appSyncConfig.url,
  region: appSyncConfig.region,
  auth: appSyncConfig.auth,
});

// Create AppSync subscription link
const appsyncSubscriptionLink = createSubscriptionHandshakeLink({
  url: appSyncConfig.url,
  region: appSyncConfig.region,
  auth: appSyncConfig.auth,
});

// Split link based on operation type (query/mutation vs subscription)
const link = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  appsyncSubscriptionLink,
  appsyncAuthLink.concat(httpLink)
);

// Create Apollo Client
const client = new ApolloClient({
  link,
  cache: new InMemoryCache(),
});

export default client;
