import axios from 'axios';

export const API_URL = 'http://localhost:53289/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DNSRecord {
  name: string;
  ttl?: number;
  content: string;
}

export interface APIResponse {
  message: string;
}

export const dnsApi = {
  createARecord: async (zoneName: string, record: DNSRecord) => {
    const response = await apiClient.post<APIResponse>(
      `/zones/${zoneName}/records/a`,
      record
    );
    return response.data;
  },

  createTXTRecord: async (zoneName: string, record: DNSRecord) => {
    const response = await apiClient.post<APIResponse>(
      `/zones/${zoneName}/records/txt`,
      record
    );
    return response.data;
  },
};