// Configuration for AWS Amplify
const config = {
    // AWS Region
    region: 'us-east-1',
    
    // Amazon Cognito
    cognito: {
        userPoolId: 'us-east-1_DQpPM15TX',
        userPoolWebClientId: '4evk2m4ru8rrenij1ukg0044k6',
        identityPoolId: 'us-east-1:dd3fed4d-d712-440a-af16-b16bf5b9c2ef',
    },
    
    // API Endpoints
    api: {
        // WebSocket API - Real-time updates, no timeout limits ✅ DEPLOYED
        websocketEndpoint: 'wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod',
        
        // Private Function URL (CORS limitations with browsers)
        privateEndpoint: 'https://bybfgjmve5b5m4baexntp62d3e0dqjty.lambda-url.us-east-1.on.aws/',
        
        // Legacy API Gateway (fallback)
        legacyEndpoint: 'https://mdog752949.execute-api.us-east-1.amazonaws.com/prod/query',
        
        // Default to WebSocket
        useWebSocket: true
    }
};

export default config;
