import { fetchAuthSession } from 'aws-amplify/auth';

class WebSocketClient {
  constructor(url, onMessage, onError, onClose, onReconnecting) {
    this.url = url;
    this.ws = null;
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
    this.onReconnecting = onReconnecting || (() => {}); // Optional callback for reconnection status
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3; // Following project rules
    this.reconnectDelay = 2000;
    this.userInfo = null;
    this.isManualClose = false;
    this.isReconnecting = false;
    this.heartbeatInterval = null;
    this.heartbeatTimeout = null;
    this.connectionPromise = null; // Track connection attempts
  }

  async connect() {
    // If already connecting, return the existing promise
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._performConnection();
    
    try {
      await this.connectionPromise;
      return true;
    } catch (error) {
      console.error('Connection failed:', error);
      return false;
    } finally {
      this.connectionPromise = null;
    }
  }

  async _performConnection() {
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

      // Return a promise that resolves when connection is established
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000); // 10 second timeout

        this.ws.onopen = (event) => {
          clearTimeout(timeout);
          this.handleOpen(event);
          resolve();
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          this.handleError(error);
          reject(error);
        };
      });

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.onError(error);
      throw error;
    }
  }

  handleOpen(event) {
    console.log('WebSocket connected successfully:', event);
    this.reconnectAttempts = 0;
    this.reconnectDelay = 2000;
    this.isReconnecting = false;
    
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

    // Start heartbeat to keep connection alive
    this.startHeartbeat();
  }

  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      console.log('WebSocket message received:', message);
      
      // Handle pong responses for heartbeat
      if (message.action === 'pong') {
        if (this.heartbeatTimeout) {
          clearTimeout(this.heartbeatTimeout);
          this.heartbeatTimeout = null;
        }
        return; // Don't pass pong messages to parent
      }
      
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
    
    // Stop heartbeat
    this.stopHeartbeat();
    
    this.onClose(event);
    
    // Only attempt to reconnect if:
    // 1. It wasn't a manual close
    // 2. We haven't exceeded max attempts
    // 3. We're not already reconnecting
    if (!this.isManualClose && 
        this.reconnectAttempts < this.maxReconnectAttempts && 
        !this.isReconnecting) {
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.isReconnecting) {
      console.log('Reconnection already in progress, skipping...');
      return;
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    // Notify parent component about reconnection attempt
    this.onReconnecting(true, this.reconnectAttempts, this.maxReconnectAttempts);
    
    setTimeout(async () => {
      if (!this.isManualClose) {
        try {
          await this.connect();
          console.log('Reconnection successful');
          this.onReconnecting(false, this.reconnectAttempts, this.maxReconnectAttempts);
        } catch (error) {
          console.error('Reconnection failed:', error);
          this.isReconnecting = false;
          
          if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            this.onReconnecting(false, this.reconnectAttempts, this.maxReconnectAttempts);
            this.onError(new Error('Max reconnection attempts reached'));
          }
        }
      } else {
        this.isReconnecting = false;
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

  async sendFinOpsQuery(query) {
    // First, ensure we have a connection
    if (!this.isConnected()) {
      console.log('WebSocket not connected, attempting to reconnect...');
      
      try {
        const connected = await this.ensureConnection();
        if (!connected) {
          throw new Error('Failed to establish WebSocket connection after reconnection attempts');
        }
      } catch (error) {
        console.error('Failed to reconnect WebSocket:', error);
        throw new Error('WebSocket connection failed - falling back to REST API');
      }
    }

    // Now send the query
    const success = this.sendMessage({
      action: 'finops_query',
      query: query,
      userId: this.userInfo?.userId || 'anonymous',
      username: this.userInfo?.username || 'anonymous',
      timestamp: Date.now()
    });
    
    if (!success) {
      throw new Error('Failed to send WebSocket message');
    }
  }

  async ensureConnection() {
    // If already connected, return true
    if (this.isConnected()) {
      return true;
    }

    // If currently reconnecting, wait for it to complete
    if (this.isReconnecting && this.connectionPromise) {
      try {
        await this.connectionPromise;
        return this.isConnected();
      } catch (error) {
        console.error('Connection attempt failed:', error);
        return false;
      }
    }

    // Attempt to connect
    try {
      const connected = await this.connect();
      return connected;
    } catch (error) {
      console.error('Failed to establish connection:', error);
      return false;
    }
  }

  // Heartbeat mechanism to keep connection alive
  startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing heartbeat
    
    // Only start heartbeat if we don't already have one running
    if (this.heartbeatInterval) {
      console.warn('Heartbeat already running, not starting another');
      return;
    }
    
    console.log('Starting WebSocket heartbeat (30 second interval)');
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        console.log('Sending heartbeat ping');
        this.sendMessage({ action: 'ping', timestamp: Date.now() });
        
        // Set timeout to detect if pong is not received
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('Heartbeat timeout - connection may be stale');
          // Don't close connection here, let natural timeout handle it
        }, 5000); // 5 second timeout for pong response
      } else {
        console.log('WebSocket not connected, stopping heartbeat');
        this.stopHeartbeat();
      }
    }, 30000); // Send ping every 30 seconds
  }

  stopHeartbeat() {
    console.log('Stopping WebSocket heartbeat');
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  disconnect() {
    this.isManualClose = true;
    this.stopHeartbeat();
    
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

  // Public method to manually trigger reconnection
  async reconnect() {
    console.log('Manual reconnection requested');
    this.reconnectAttempts = 0; // Reset attempts for manual reconnection
    this.isManualClose = false;
    
    if (this.ws) {
      this.ws.close(1000, 'Manual reconnect');
    }
    
    try {
      const connected = await this.connect();
      return connected;
    } catch (error) {
      console.error('Manual reconnection failed:', error);
      return false;
    }
  }
}

export default WebSocketClient;
