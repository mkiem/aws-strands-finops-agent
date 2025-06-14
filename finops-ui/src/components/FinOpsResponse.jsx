import React from 'react';
import ReactMarkdown from 'react-markdown';
import './FinOpsResponse.css';

const StreamingAgentResult = ({ agent, result, isCompleted }) => {
  if (!result) {
    return (
      <div className="streaming-agent-section loading">
        <div className="agent-header">
          <h3>{result?.title || `${agent} Analysis`}</h3>
          <div className="loading-spinner">⏳</div>
        </div>
        <div className="loading-placeholder">
          <div className="skeleton-line"></div>
          <div className="skeleton-line"></div>
          <div className="skeleton-line short"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`streaming-agent-section ${result.status === 'error' ? 'error' : 'completed'}`}>
      <div className="agent-header">
        <h3>{result.title}</h3>
        <div className="agent-status">
          {result.status === 'completed' ? '✅' : '❌'}
        </div>
      </div>
      <div className="agent-content">
        <ReactMarkdown>{result.content}</ReactMarkdown>
      </div>
      {result.timestamp && (
        <div className="agent-timestamp">
          Completed at {new Date(result.timestamp * 1000).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

const FinOpsResponse = ({ responseData }) => {
  if (!responseData) {
    return null;
  }

  // Handle streaming responses
  if (responseData.type === 'streaming') {
    const { 
      agents, 
      routing_explanation, 
      results, 
      completed_agents, 
      total_agents, 
      final_response, 
      completed,
      start_time 
    } = responseData;

    return (
      <div className="finops-response streaming">
        <div className="response-header">
          <h2>🏦 AWS FinOps Analysis</h2>
          <div className="streaming-progress">
            {completed ? (
              <span className="completed">✅ Analysis Complete ({completed_agents.length}/{total_agents} agents)</span>
            ) : (
              <span className="in-progress">⏳ Processing ({completed_agents.length}/{total_agents} agents)</span>
            )}
          </div>
        </div>

        {routing_explanation && (
          <div className="routing-explanation">
            <ReactMarkdown>{routing_explanation}</ReactMarkdown>
          </div>
        )}

        <div className="streaming-results">
          {agents.map(agent => (
            <StreamingAgentResult
              key={agent}
              agent={agent}
              result={results[agent]}
              isCompleted={completed_agents.includes(agent)}
            />
          ))}
        </div>

        {completed && final_response && (
          <div className="final-summary">
            <h3>📋 Complete Analysis</h3>
            <ReactMarkdown>{final_response}</ReactMarkdown>
          </div>
        )}

        {start_time && (
          <div className="analysis-timing">
            Processing time: {completed ? 
              `${((Date.now() - start_time) / 1000).toFixed(1)}s` : 
              `${((Date.now() - start_time) / 1000).toFixed(1)}s (ongoing)`
            }
          </div>
        )}
      </div>
    );
  }

  // Handle traditional responses (existing logic)
  const { query, response } = responseData;

  // Check if response is an array of text chunks
  const isArrayResponse = Array.isArray(response);

  // Function to extract and combine markdown content
  const getMarkdownContent = () => {
    if (!response) {
      return "No response available";
    }
    
    if (isArrayResponse) {
      // Combine all text chunks into a single string
      return response.map(chunk => chunk.text || '').join('');
    } else if (typeof response === 'string') {
      // If response is already a string, return it directly
      return response;
    } else if (response.error) {
      // Handle error responses
      return `Error: ${response.error}`;
    } else {
      // If response is some other format, stringify it
      return JSON.stringify(response, null, 2);
    }
  };

  // Extract cost information for the cost summary card
  const extractCostInfo = () => {
    const markdownContent = getMarkdownContent();
    
    // Default values
    let costInfo = {
      serviceName: "AWS",
      costAmount: "0.00",
      timePeriod: ""
    };
    
    // Safety check for markdownContent
    if (!markdownContent || typeof markdownContent !== 'string') {
      return costInfo;
    }
    
    // Try to extract service name from first heading
    const serviceMatch = markdownContent.match(/# (.*?) Cost/);
    if (serviceMatch) {
      costInfo.serviceName = serviceMatch[1];
    }
    
    // Enhanced cost extraction logic
    const extractCostAmount = () => {
      // Priority 1: Look for "Total" amounts (most important)
      const totalPatterns = [
        /Total.*?\$([0-9,]+\.?\d*)/gi,
        /Total.*?\$([0-9,]+)/gi,
        /\$([0-9,]+\.?\d*).*?total/gi,
        /Grand Total.*?\$([0-9,]+\.?\d*)/gi,
        /Overall.*?\$([0-9,]+\.?\d*)/gi
      ];
      
      for (const pattern of totalPatterns) {
        const matches = [...markdownContent.matchAll(pattern)];
        if (matches.length > 0) {
          // Get the largest total amount found
          const amounts = matches.map(match => parseFloat(match[1].replace(/,/g, '')));
          const maxAmount = Math.max(...amounts);
          return maxAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
      }
      
      // Priority 2: Look for summary or aggregate amounts
      const summaryPatterns = [
        /Summary.*?\$([0-9,]+\.?\d*)/gi,
        /\$([0-9,]+\.?\d*).*?summary/gi,
        /Aggregate.*?\$([0-9,]+\.?\d*)/gi,
        /Combined.*?\$([0-9,]+\.?\d*)/gi
      ];
      
      for (const pattern of summaryPatterns) {
        const matches = [...markdownContent.matchAll(pattern)];
        if (matches.length > 0) {
          const amounts = matches.map(match => parseFloat(match[1].replace(/,/g, '')));
          const maxAmount = Math.max(...amounts);
          return maxAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
      }
      
      // Priority 3: Look for the largest dollar amount (likely the total)
      const allAmountPattern = /\$([0-9,]+\.?\d*)/g;
      const allMatches = [...markdownContent.matchAll(allAmountPattern)];
      
      if (allMatches.length > 0) {
        // Parse all amounts and find the largest (most likely to be the total)
        const amounts = allMatches.map(match => {
          const cleanAmount = match[1].replace(/,/g, '');
          return parseFloat(cleanAmount);
        }).filter(amount => !isNaN(amount));
        
        if (amounts.length > 0) {
          const maxAmount = Math.max(...amounts);
          // Only use if it's a reasonable amount (> $1)
          if (maxAmount > 1) {
            return maxAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          }
        }
      }
      
      // Priority 4: Fallback to original simple pattern
      const simpleMatch = markdownContent.match(/\$(\d+\.?\d*)/);
      if (simpleMatch) {
        const amount = parseFloat(simpleMatch[1]);
        return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }
      
      return "0.00";
    };
    
    costInfo.costAmount = extractCostAmount();
    
    // Try to extract time period
    const timeMatch = markdownContent.match(/Time Period\*\*: (.*?)(\n|$)/);
    if (timeMatch) {
      costInfo.timePeriod = timeMatch[1];
    }
    
    return costInfo;
  };

  // Get the markdown content and cost info
  const markdownContent = getMarkdownContent();
  const costInfo = extractCostInfo();

  return (
    <div className="finops-response-container">
      <div className="query-section">
        <h3>Your Question:</h3>
        <p>{query}</p>
      </div>
      
      <div className="cost-summary-card">
        <div className="service-name">{costInfo.serviceName} Cost Summary</div>
        <div className="cost-amount">${costInfo.costAmount}</div>
        {costInfo.timePeriod && <div className="time-period">{costInfo.timePeriod}</div>}
      </div>
      
      <div className="response-section">
        <ReactMarkdown>{markdownContent}</ReactMarkdown>
      </div>
    </div>
  );
};

export default FinOpsResponse;
