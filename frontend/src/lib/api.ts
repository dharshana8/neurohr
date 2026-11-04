import axios from 'axios';

export const api = {
  get: (url: string) => axios.get(`http://localhost:8000/api/v1${url}`),
  post: (url: string, data?: any) => axios.post(`http://localhost:8000/api/v1${url}`, data),
  put: (url: string, data?: any) => axios.put(`http://localhost:8000/api/v1${url}`, data),
  delete: (url: string) => axios.delete(`http://localhost:8000/api/v1${url}`),
};
