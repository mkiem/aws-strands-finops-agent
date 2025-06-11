import { fetchAuthSession } from 'aws-amplify/auth';
import { SignatureV4 } from '@aws-sdk/signature-v4';
import { HttpRequest } from '@aws-sdk/protocol-http';
import { Sha256 } from '@aws-crypto/sha256-browser';

/**
 * Make a signed request to AWS Lambda Function URL
 * @param {string} url - The Lambda Function URL
 * @param {Object} payload - The request payload
 * @param {string} method - HTTP method (default: POST)
 * @returns {Promise<Response>} - Fetch response
 */
export async function makeSignedRequest(url, payload, method = 'POST') {
  try {
    // Get current AWS credentials from Cognito
    const session = await fetchAuthSession();
    const credentials = session.credentials;
    
    if (!credentials || !credentials.accessKeyId) {
      throw new Error('No valid AWS credentials found. Please ensure you are authenticated.');
    }

    // Parse the URL
    const urlObj = new URL(url);
    
    // Create the HTTP request
    const request = new HttpRequest({
      method: method,
      hostname: urlObj.hostname,
      path: urlObj.pathname,
      headers: {
        'Content-Type': 'application/json',
        'host': urlObj.hostname,
      },
      body: JSON.stringify(payload)
    });

    // Create the signer
    const signer = new SignatureV4({
      credentials: {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      },
      region: 'us-east-1',
      service: 'lambda',
      sha256: Sha256
    });

    // Sign the request
    const signedRequest = await signer.sign(request);

    // Convert signed request to fetch options
    const fetchOptions = {
      method: signedRequest.method,
      headers: {},
      body: signedRequest.body
    };

    // Copy headers from signed request
    for (const [key, value] of Object.entries(signedRequest.headers)) {
      fetchOptions.headers[key] = value;
    }

    console.log('Making signed request to:', url);
    console.log('Request headers:', fetchOptions.headers);

    // Make the actual fetch request
    const response = await fetch(url, fetchOptions);
    
    return response;

  } catch (error) {
    console.error('Error making signed request:', error);
    throw error;
  }
}

/**
 * Make a regular unsigned request (for API Gateway)
 * @param {string} url - The API Gateway URL
 * @param {Object} payload - The request payload
 * @param {string} method - HTTP method (default: POST)
 * @returns {Promise<Response>} - Fetch response
 */
export async function makeUnsignedRequest(url, payload, method = 'POST') {
  const response = await fetch(url, {
    method: method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });
  
  return response;
}
