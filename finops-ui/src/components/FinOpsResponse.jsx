import React from 'react';
import ReactMarkdown from 'react-markdown';
import './FinOpsResponse.css';

const FinOpsResponse = ({ responseData }) => {
  if (!responseData) {
    return null;
  }

  // Extract the query and response from the data
  const { query, response } = responseData;

  // Check if response is an array of text chunks
  const isArrayResponse = Array.isArray(response);

  // Function to extract and combine markdown content
  const getMarkdownContent = () => {
    if (isArrayResponse) {
      // Combine all text chunks into a single string
      return response.map(chunk => chunk.text || '').join('');
    } else if (typeof response === 'string') {
      // If response is already a string, return it directly
      return response;
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
    
    // Try to extract service name from first heading
    const serviceMatch = markdownContent.match(/# (.*?) Cost/);
    if (serviceMatch) {
      costInfo.serviceName = serviceMatch[1];
    }
    
    // Try to extract cost amount
    const costMatch = markdownContent.match(/\$(\d+\.\d+)/);
    if (costMatch) {
      costInfo.costAmount = costMatch[1];
    }
    
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
