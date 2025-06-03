import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Amplify } from 'aws-amplify';
import awsconfig from './aws-exports';

// If aws-exports.js doesn't exist yet, we'll use a placeholder configuration
// You'll need to replace this with your actual configuration after running 'amplify init'
let config = awsconfig;
try {
  config = awsconfig;
} catch (e) {
  // Fallback configuration - replace with your actual values when deploying
  config = {
    Auth: {
      region: 'us-east-1',
      userPoolId: 'REPLACE_WITH_USER_POOL_ID',
      userPoolWebClientId: 'REPLACE_WITH_USER_POOL_CLIENT_ID',
      mandatorySignIn: true,
    },
    API: {
      endpoints: [
        {
          name: 'finopsAgentAPI',
          endpoint: 'REPLACE_WITH_API_GATEWAY_URL',
          region: 'us-east-1'
        }
      ]
    }
  };
}

Amplify.configure(config);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
