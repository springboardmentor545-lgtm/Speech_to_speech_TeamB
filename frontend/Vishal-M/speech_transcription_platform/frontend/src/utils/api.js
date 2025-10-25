import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // Increased timeout for potentially long operations
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Add a response interceptor for centralized error handling
api.interceptors.response.use(
  (response) => response, // Simply return successful responses
  (error) => {
    // Log the error for debugging
    console.error('API Error:', error.response || error.message || error);

    // Extract a user-friendly error message
    const message = error.response?.data?.detail || // FastAPI HTTPExceptions
                    error.message ||               // Network errors or others
                    'An unexpected error occurred.';

    // You could potentially trigger a global notification system here
    // e.g., showToast(message, 'error');

    // Reject the promise so component-level error handlers can catch it
    return Promise.reject({
        message: message,
        status: error.response?.status,
        data: error.response?.data
    });
  }
)

export default api
