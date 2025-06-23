/**
 * API Configuration utility
 * Uses environment variables to configure the backend URL for different environments
 */

// Get the API base URL from environment variables
// In development: http://localhost:8000
// In production: your deployed backend URL
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch wrapper with default configuration for API calls
 */
export const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  getDownloadUrl(downloadUrl: string) {
    return `${API_BASE_URL}${downloadUrl}`;
  }
};

// Export the base URL for direct use
export { API_BASE_URL as default }; 