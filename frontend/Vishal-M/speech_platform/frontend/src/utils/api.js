// This self-contained API helper can be imported by Milestone1.jsx, Milestone2.jsx, etc.
// It mimics the axios API structure for easy integration.

const api = {
  get: async (url, config = {}) => {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...config.headers,
      },
      ...config,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw { response: { data: errorData } }; // Mimic axios error structure
    }

    if (config.responseType === 'blob') {
      return {
        data: await response.blob(),
        headers: response.headers,
      };
    }
    
    return { data: await response.json() };
  },
  
  post: (url, data, config = {}) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url, true);

      if (config.headers) {
        Object.entries(config.headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value);
        });
      }
      
      const isFormData = data instanceof FormData;
      if (!isFormData) {
         xhr.setRequestHeader('Content-Type', 'application/json');
         xhr.setRequestHeader('Accept', 'application/json');
      }

      if (config.onUploadProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            config.onUploadProgress(event);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve({ data: JSON.parse(xhr.responseText) });
          } catch(e) {
            reject({ response: { data: { detail: 'Invalid JSON response from server.' } } });
          }
        } else {
          let errorData;
          try {
            errorData = JSON.parse(xhr.responseText);
          } catch (e) {
            errorData = { detail: xhr.statusText };
          }
          reject({ response: { data: errorData } });
        }
      };

      xhr.onerror = () => {
        reject({ response: { data: { detail: 'Network error' } } });
      };

      const body = isFormData ? data : JSON.stringify(data);
      xhr.send(body);
    });
  },
};

export default api;