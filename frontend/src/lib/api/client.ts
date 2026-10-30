// API Client for FastAPI Backend

const API_URL = import.meta.env.PUBLIC_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    let url = cleanEndpoint;
    if (this.baseURL) {
      const base = this.baseURL.replace(/\/$/, '');
      if (base.endsWith('/api') && cleanEndpoint.startsWith('/api/')) {
        url = `${base}${cleanEndpoint.slice(4)}`;
      } else {
        url = `${base}${cleanEndpoint}`;
      }
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`Connection failed: Unable to reach API at ${url}. Make sure the backend server is running.`);
      }
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new APIClient();
