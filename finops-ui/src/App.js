import React, { useState, useEffect, useRef } from 'react';
import { Amplify } from 'aws-amplify';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import './App.css';
import config from './config';
import FinOpsResponse from './components/FinOpsResponse';
import { makeSignedRequest, makeUnsignedRequest } from './utils/awsRequest';
import WebSocketClient from './utils/websocketClient';

// Configure Amplify with correct auth configuration
Amplify.configure({
  aws_project_region: config.region,
  aws_cognito_region: config.region,
  aws_user_pools_id: config.cognito.userPoolId,
  aws_user_pools_web_client_id: config.cognito.userPoolWebClientId,
  aws_cognito_identity_pool_id: config.cognito.identityPoolId,
  aws_mandatory_sign_in: 'enable',
  Auth: {
    region: config.region,
    userPoolId: config.cognito.userPoolId,
    userPoolWebClientId: config.cognito.userPoolWebClientId,
    identityPoolId: config.cognito.identityPoolId,
    mandatorySignIn: true,
    authenticationFlowType: 'USER_SRP_AUTH'
  }
});

function App({ signOut, user }) {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [wsStatus, setWsStatus] = useState('DISCONNECTED');
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [currentJobId, setCurrentJobId] = useState(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [reconnectionInfo, setReconnectionInfo] = useState({ attempts: 0, maxAttempts: 0 });
  
  const wsClient = useRef(null);

  // WebSocket event handlers
  const handleWebSocketMessage = (message) => {
    console.log('WebSocket message:', message);
    
    switch (message.type) {
      case 'job_queued':
        setCurrentJobId(message.jobId);
        setProgress(5);
        setProgressMessage(message.message);
        break;
        
      case 'progress_update':
        setProgress(message.progress);
        setProgressMessage(message.message);
        break;
        
      case 'job_completed':
        setLoading(false);
        setProgress(100);
        setProgressMessage('Analysis completed!');
        setResponse(message.result);
        setCurrentJobId(null);
        break;
        
      case 'job_failed':
        setLoading(false);
        setError(`Job failed: ${message.error}`);
        setProgress(0);
        setProgressMessage('');
        setCurrentJobId(null);
        break;
        
      case 'error':
        setError(message.message);
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const handleWebSocketError = (error) => {
    console.error('WebSocket error:', error);
    setError(`WebSocket error: ${error.message}`);
  };

  const handleWebSocketClose = (event) => {
    console.log('WebSocket closed:', event);
    setWsStatus('DISCONNECTED');
    setIsReconnecting(false); // Reset reconnecting state when connection closes
  };

  const handleWebSocketReconnecting = (reconnecting, attempts, maxAttempts) => {
    setIsReconnecting(reconnecting);
    setReconnectionInfo({ attempts, maxAttempts });
    
    if (reconnecting) {
      setWsStatus('RECONNECTING');
    } else if (attempts >= maxAttempts) {
      setWsStatus('FAILED');
      setError('WebSocket connection failed after multiple attempts. Using REST API fallback.');
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    if (useWebSocket && config.api.websocketEndpoint) {
      wsClient.current = new WebSocketClient(
        config.api.websocketEndpoint,
        handleWebSocketMessage,
        handleWebSocketError,
        handleWebSocketClose,
        handleWebSocketReconnecting
      );
      
      wsClient.current.connect();
      
      // Update connection status
      const statusInterval = setInterval(() => {
        if (wsClient.current) {
          const currentStatus = wsClient.current.getConnectionState();
          // Only update status if not currently reconnecting
          if (!isReconnecting || currentStatus === 'CONNECTED') {
            setWsStatus(currentStatus);
          }
        }
      }, 1000);
      
      return () => {
        clearInterval(statusInterval);
        if (wsClient.current) {
          wsClient.current.disconnect();
        }
      };
    }
  }, [useWebSocket, isReconnecting]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setProgress(0);
    setProgressMessage('');

    try {
      if (useWebSocket && wsClient.current) {
        // Always try WebSocket first - let the client handle reconnection
        console.log('Attempting WebSocket query...');
        setProgressMessage('Connecting to WebSocket...');
        
        try {
          await wsClient.current.sendFinOpsQuery(query);
          setProgressMessage('Query sent via WebSocket...');
        } catch (wsError) {
          console.warn('WebSocket failed, falling back to REST API:', wsError);
          setError(null); // Clear any previous errors
          
          // Fall back to REST API
          console.log('Using REST API fallback');
          let apiResponse = await makeUnsignedRequest(config.api.legacyEndpoint, { query });

          if (!apiResponse.ok) {
            throw new Error(`HTTP error! status: ${apiResponse.status}`);
          }

          const responseText = await apiResponse.text();
          console.log('API Raw Response:', responseText);

          let parsedResponse;
          try {
            parsedResponse = JSON.parse(responseText);
            console.log('Parsed Response:', parsedResponse);
            
            // Handle different response formats
            if (parsedResponse.body && typeof parsedResponse.body === 'string') {
              try {
                const bodyObj = JSON.parse(parsedResponse.body);
                setResponse(bodyObj);
              } catch (e) {
                setResponse({ 
                  query: query,
                  response: parsedResponse.body 
                });
              }
            } else if (parsedResponse.body && typeof parsedResponse.body === 'object') {
              setResponse(parsedResponse.body);
            } else {
              setResponse(parsedResponse);
            }
          } catch (e) {
            setResponse({ 
              query: query,
              response: responseText 
            });
          }
          
          setLoading(false);
        }
        
      } else {
        // WebSocket disabled, use REST API
        console.log('WebSocket disabled, using REST API');
        let apiResponse = await makeUnsignedRequest(config.api.legacyEndpoint, { query });

        if (!apiResponse.ok) {
          throw new Error(`HTTP error! status: ${apiResponse.status}`);
        }

        const responseText = await apiResponse.text();
        console.log('API Raw Response:', responseText);

        let parsedResponse;
        try {
          parsedResponse = JSON.parse(responseText);
          console.log('Parsed Response:', parsedResponse);
          
          // Handle different response formats
          if (parsedResponse.body && typeof parsedResponse.body === 'string') {
            try {
              const bodyObj = JSON.parse(parsedResponse.body);
              setResponse(bodyObj);
            } catch (e) {
              setResponse({ 
                query: query,
                response: parsedResponse.body 
              });
            }
          } else if (parsedResponse.body && typeof parsedResponse.body === 'object') {
            setResponse(parsedResponse.body);
          } else {
            setResponse(parsedResponse);
          }
        } catch (e) {
          setResponse({ 
            query: query,
            response: responseText 
          });
        }
        
        setLoading(false);
      }
      
    } catch (error) {
      console.error('Error querying FinOps agent:', error);
      setError(error.message);
      setLoading(false);
      setProgress(0);
      setProgressMessage('');
    }
  };

  // Manual reconnection handler
  const handleManualReconnect = async () => {
    if (wsClient.current) {
      setError(null);
      setIsReconnecting(true);
      setWsStatus('RECONNECTING');
      
      try {
        const connected = await wsClient.current.reconnect();
        if (connected) {
          setWsStatus('CONNECTED');
          setIsReconnecting(false);
        } else {
          setWsStatus('FAILED');
          setIsReconnecting(false);
          setError('Failed to reconnect WebSocket');
        }
      } catch (error) {
        console.error('Manual reconnection failed:', error);
        setWsStatus('FAILED');
        setIsReconnecting(false);
        setError('Manual reconnection failed');
      }
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="header-main">
            <div className="header-icon">💰</div>
            <div className="header-text">
              <h1>AWS FinOps Agent</h1>
              <p className="header-subtitle">Intelligent Financial Operations & Cost Optimization</p>
            </div>
          </div>
          <div className="user-info">
            <span className="welcome-text">Welcome, {user.username}!</span>
            <button onClick={signOut} className="sign-out-btn">Sign out</button>
          </div>
        </div>
      </header>

      <main className="App-main">
        <div className="query-section">
          <div className="query-container">
            <h2 className="query-title">What would you like to analyze?</h2>
            <form onSubmit={onSubmit} className="query-form">
              <div className="input-group">
                <div className="input-wrapper">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about your AWS costs, optimization opportunities, budget forecasts, or financial insights..."
                    className="query-input"
                    disabled={loading}
                    rows="3"
                  />
                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={loading || !query.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="btn-spinner"></span>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <span className="btn-icon">🚀</span>
                        Analyze Now
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {loading && useWebSocket && (
          <div className="progress-section">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="progress-message">
              {progressMessage} ({progress}%)
              {currentJobId && <small><br />Job ID: {currentJobId}</small>}
            </p>
          </div>
        )}

        {error && (
          <div className="error-section">
            <h3>❌ Error</h3>
            <pre style={{whiteSpace: 'pre-wrap'}}>{error}</pre>
          </div>
        )}

        {response && (
          <div className="response-section">
            <FinOpsResponse responseData={response} />
          </div>
        )}

        {loading && !useWebSocket && (
          <div className="loading-section">
            <div className="loading-spinner"></div>
            <p>🔄 Analyzing with API Gateway (29s timeout limit)...</p>
          </div>
        )}
      </main>

      {/* WebSocket Status Footer */}
      <footer className="websocket-footer">
        <div className="endpoint-selector">
          <label>
            <input
              type="checkbox"
              checked={useWebSocket}
              onChange={(e) => setUseWebSocket(e.target.checked)}
            />
            <span className="checkbox-label">Use WebSocket API - Real-time Updates, No Timeout Limits</span>
          </label>
          <div className="connection-status">
            {useWebSocket ? (
              <div>
                <small className={`status-indicator ${wsStatus.toLowerCase()}`}>
                  {wsStatus === 'CONNECTED' && '✅ WebSocket: Connected - Real-time updates active'}
                  {wsStatus === 'CONNECTING' && '🔄 WebSocket: Connecting...'}
                  {wsStatus === 'RECONNECTING' && `🔄 WebSocket: Reconnecting (${reconnectionInfo.attempts}/${reconnectionInfo.maxAttempts})...`}
                  {wsStatus === 'DISCONNECTED' && '⚠️ WebSocket: Disconnected - Will auto-reconnect on next query'}
                  {wsStatus === 'FAILED' && '❌ WebSocket: Connection failed - Using REST API fallback'}
                </small>
                {(wsStatus === 'DISCONNECTED' || wsStatus === 'FAILED') && (
                  <button 
                    onClick={handleManualReconnect} 
                    className="reconnect-btn"
                    disabled={isReconnecting}
                  >
                    {isReconnecting ? 'Reconnecting...' : 'Reconnect Now'}
                  </button>
                )}
              </div>
            ) : (
              <small className="status-indicator legacy">⚠️ Using legacy API Gateway (29s timeout limit)</small>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default withAuthenticator(App);
