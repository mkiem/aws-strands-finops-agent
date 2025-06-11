import { fetchAuthSession } from 'aws-amplify/auth';

class WebSocketClient {
  constructor(url, onMessage, onError, onClose) {
    this.url = url;
    this.ws = null;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3; // Reduced to avoid infinite loops
    this.reconnectDelay = 2000; // Increased initial delay
    this.userInfo = null;
    this.isManualClose = false;
  }

  async connect() {
    try {
      // Get user information for connection context
      const session = await fetchAuthSession();
      this.userInfo = {
        userId: session.tokens?.idToken?.payload?.sub || 'anonymous',
        username: session.tokens?.idToken?.payload['cognito:username'] || 'anonymous'
      };
      
      console.log('Connecting WebSocket for user:', this.userInfo);

      // Reset manual close flag
      this.isManualClose = false;

      // Create WebSocket connection without token in URL
      this.ws = new WebSocket(this.url);

      // Set up event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.onError(error);
    }
  }

  handleOpen(event) {
    console.log('WebSocket connected successfully:', event);
    this.reconnectAttempts = 0;
    this.reconnectDelay = 2000;
    
    // Send user info after connection is established
    setTimeout(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({
          action: 'authenticate',
          userId: this.userInfo.userId,
          username: this.userInfo.username
        });
      }
    }, 100); // Small delay to ensure connection is fully established
  }

  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('WebSocket message received:', message);
      this.onMessage(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      this.onError(error);
    }
  }

  handleError(error) {
    console.error('WebSocket error:', error);
    this.onError(error);
  }

  handleClose(event) {
    console.log('WebSocket closed:', event);
    console.log('Close code:', event.code, 'Reason:', event.reason, 'Clean:', event.wasClean);
    
    this.onClose(event);
    
    // Only attempt to reconnect if:
    // 1. It wasn't a manual close
    // 2. We haven't exceeded max attempts
    // 3. The close wasn't clean (indicating an error)
    if (!this.isManualClose && 
        this.reconnectAttempts < this.maxReconnectAttempts && 
        (!event.wasClean || event.code === 1006)) {
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect();
      }
    }, this.reconnectDelay);
    
    // Exponential backoff with max limit
    this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 10000); // Max 10 seconds
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log('WebSocket message sent:', message);
      return true;
    } else {
      console.error('WebSocket is not connected. State:', this.getConnectionState());
      return false;
    }
  }

  sendFinOpsQuery(query) {
    const success = this.sendMessage({
      action: 'finops_query',
      query: query,
      userId: this.userInfo?.userId || 'anonymous',
      username: this.userInfo?.username || 'anonymous',
      timestamp: Date.now()
    });
    
    if (!success) {
      throw new Error('WebSocket is not connected');
    }
  }

  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  getConnectionState() {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'DISCONNECTED';
      default:
        return 'UNKNOWN';
    }
  }
}

export default WebSocketClient;
