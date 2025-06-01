import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [drivingStatus, setDrivingStatus] = useState('parked');
  const messagesEndRef = useRef(null);

  // Generate session ID on first load
  useEffect(() => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    setSessionId(newSessionId);
  }, []);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send welcome message
  useEffect(() => {
    if (sessionId) {
      setMessages([{
        id: 'welcome',
        message: '',
        response: "Hello! I'm your AI car assistant. I can help you with car maintenance, performance optimization, troubleshooting, and driving advice. What would you like to know about your vehicle?",
        timestamp: new Date().toISOString(),
        isWelcome: true
      }]);
    }
  }, [sessionId]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !sessionId) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message to UI immediately
    const tempMessage = {
      id: 'temp_' + Date.now(),
      message: userMessage,
      response: '',
      timestamp: new Date().toISOString(),
      isUser: true
    };
    setMessages(prev => [...prev, tempMessage]);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
          driving_status: drivingStatus
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      // Replace temp message with actual response
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id 
          ? {
              id: data.message_id,
              message: userMessage,
              response: data.response,
              timestamp: new Date().toISOString(),
              isUser: false
            }
          : msg
      ));

    } catch (error) {
      console.error('Error sending message:', error);
      // Replace temp message with error
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id 
          ? {
              ...msg,
              response: 'Sorry, I encountered an error. Please try again.',
              isError: true
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getDrivingStatusIcon = (status) => {
    const icons = {
      parked: '🅿️',
      city_driving: '🏙️',
      highway: '🛣️',
      traffic: '🚦'
    };
    return icons[status] || '🚗';
  };

  const getDrivingStatusLabel = (status) => {
    const labels = {
      parked: 'Parked',
      city_driving: 'City Driving',
      highway: 'Highway',
      traffic: 'In Traffic'
    };
    return labels[status] || 'Unknown';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-3">
                <span className="text-2xl">🚗</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Car Assistant</h1>
                <p className="text-gray-600">Your intelligent automotive companion</p>
              </div>
            </div>
            
            {/* Driving Status Selector */}
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <select
                value={drivingStatus}
                onChange={(e) => setDrivingStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="parked">🅿️ Parked</option>
                <option value="city_driving">🏙️ City Driving</option>
                <option value="highway">🛣️ Highway</option>
                <option value="traffic">🚦 In Traffic</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Messages Area */}
          <div className="h-96 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={msg.id}
                className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                    msg.isUser
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                      : msg.isWelcome
                      ? 'bg-gradient-to-r from-green-100 to-blue-100 text-gray-800 border border-green-200'
                      : msg.isError
                      ? 'bg-red-100 text-red-800 border border-red-200'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {msg.isUser ? (
                    <p className="text-sm">{msg.message}</p>
                  ) : (
                    <div>
                      {msg.isWelcome && (
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-lg">🤖</span>
                          <span className="text-xs font-semibold text-green-700">Assistant</span>
                        </div>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{msg.response}</p>
                    </div>
                  )}
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl px-4 py-3 max-w-xs">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                    <span className="text-xs text-gray-500">Assistant is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about car maintenance, performance tips, or any automotive question..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows="2"
                  disabled={isLoading}
                />
                <div className="absolute right-3 bottom-3 text-xs text-gray-400">
                  Press Enter to send
                </div>
              </div>
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
            
            {/* Status indicator */}
            <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                <span>Connected</span>
                <span>•</span>
                <span>Current status: {getDrivingStatusIcon(drivingStatus)} {getDrivingStatusLabel(drivingStatus)}</span>
              </div>
              <div>
                Session: {sessionId?.substring(0, 8)}...
              </div>
            </div>
          </div>
        </div>

        {/* Quick Tips */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🔧</span>
              <div>
                <h3 className="font-semibold text-gray-900">Maintenance</h3>
                <p className="text-sm text-gray-600">Get maintenance schedules and tips</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-4 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">⚡</span>
              <div>
                <h3 className="font-semibold text-gray-900">Performance</h3>
                <p className="text-sm text-gray-600">Optimize your car's performance</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-4 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🛣️</span>
              <div>
                <h3 className="font-semibold text-gray-900">Driving Tips</h3>
                <p className="text-sm text-gray-600">Context-aware driving advice</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
