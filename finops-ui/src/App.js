import React, { useState } from 'react';
import { Amplify } from 'aws-amplify';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import './App.css';
import awsconfig from './aws-exports';

// Configure Amplify
Amplify.configure(awsconfig);

function App({ signOut, user }) {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [debug, setDebug] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setDebug('');
    
    try {
      // Make a direct fetch call to the API Gateway endpoint
      const apiUrl = 'https://71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod/query';
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      };
      
      console.log('Sending request to:', apiUrl);
      console.log('Request options:', requestOptions);
      
      const fetchResponse = await fetch(apiUrl, requestOptions);
      const responseText = await fetchResponse.text(); // Get response as text first
      
      // Debug information
      setDebug(JSON.stringify({
        status: fetchResponse.status,
        statusText: fetchResponse.statusText,
        headers: Object.fromEntries([...fetchResponse.headers.entries()]),
        rawResponse: responseText
      }, null, 2));
      
      console.log('API Raw Response:', responseText);
      
      // Try to parse the response as JSON
      let parsedResponse;
      let formattedResponse = '';
      
      try {
        parsedResponse = JSON.parse(responseText);
        console.log('Parsed Response:', parsedResponse);
        
        // Handle different response formats
        if (parsedResponse.body && typeof parsedResponse.body === 'string') {
          try {
            // Try to parse the body if it's a JSON string
            const bodyObj = JSON.parse(parsedResponse.body);
            if (bodyObj.response) {
              formattedResponse = bodyObj.response;
            } else if (bodyObj.query && bodyObj.response) {
              formattedResponse = bodyObj.response;
            } else {
              formattedResponse = JSON.stringify(bodyObj, null, 2);
            }
          } catch (e) {
            // If body is not JSON, use it directly
            formattedResponse = parsedResponse.body;
          }
        } else if (parsedResponse.body && typeof parsedResponse.body === 'object') {
          // If body is already an object
          if (parsedResponse.body.response) {
            formattedResponse = parsedResponse.body.response;
          } else {
            formattedResponse = JSON.stringify(parsedResponse.body, null, 2);
          }
        } else if (parsedResponse.message) {
          // For test Lambda format
          formattedResponse = parsedResponse.message;
          if (parsedResponse.input && parsedResponse.input.body) {
            try {
              const inputBody = JSON.parse(parsedResponse.input.body);
              formattedResponse += "\n\nInput: " + JSON.stringify(inputBody, null, 2);
            } catch (e) {
              formattedResponse += "\n\nInput: " + parsedResponse.input.body;
            }
          }
        } else {
          // Default fallback
          formattedResponse = JSON.stringify(parsedResponse, null, 2);
        }
      } catch (e) {
        // If response is not valid JSON
        console.error('Error parsing response:', e);
        formattedResponse = responseText;
      }
      
      setResponse(formattedResponse);
      
      // Add to history
      setHistory([
        { query, response: formattedResponse, timestamp: new Date().toISOString() },
        ...history
      ]);
      
      // Clear the input
      setQuery('');
    } catch (error) {
      console.error('Error querying FinOps agent:', error);
      setResponse(`Error: Failed to get a response from the FinOps agent.\n\nDetails: ${error.message}`);
      setDebug(JSON.stringify(error, null, 2));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FinOps Agent Dashboard</h1>
        <p>Ask questions about your AWS costs and optimization opportunities</p>
        <div className="user-info">
          <span>Welcome, {user.username}</span>
          <button onClick={signOut} className="sign-out-button">Sign out</button>
        </div>
      </header>
      
      <main>
        <form onSubmit={handleSubmit} className="query-form">
          <div className="input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What is my current AWS spend?"
              required
              className="query-input"
            />
            <button type="submit" disabled={loading} className="query-button">
              {loading ? 'Thinking...' : 'Ask'}
            </button>
          </div>
        </form>
        
        {response && (
          <div className="response-container">
            <h2>Response:</h2>
            <div className="response-content">
              {response}
            </div>
          </div>
        )}
        
        {debug && (
          <div className="debug-container">
            <h3>Debug Information:</h3>
            <pre className="debug-content">
              {debug}
            </pre>
          </div>
        )}
        
        {history.length > 0 && (
          <div className="history-container">
            <h2>Query History</h2>
            <div className="history-list">
              {history.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-query">
                    <strong>Q:</strong> {item.query}
                  </div>
                  <div className="history-response">
                    <strong>A:</strong> {item.response.substring(0, 100)}
                    {item.response.length > 100 ? '...' : ''}
                  </div>
                  <div className="history-timestamp">
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
      
      <footer className="App-footer">
        <p>FinOps Agent powered by AWS Lambda and Strands SDK</p>
      </footer>
    </div>
  );
}

// Export with authentication wrapper
export default withAuthenticator(App);
