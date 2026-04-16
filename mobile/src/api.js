import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Change this to your backend URL
const API_BASE_URL = 'https://scrolluforward-production.up.railway.app';
// Local dev: const API_BASE_URL = 'http://192.168.1.60:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Bypass-Tunnel-Reminder': 'true',
    'ngrok-skip-browser-warning': 'true',
  },
});

// Attach auth token to every request
api.interceptors.request.use(async (config) => {
  try {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (e) { }
  return config;
});

// ─── Auth ────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  getMe: () => api.get('/auth/me/'),
  google: (data) => api.post('/auth/google', data),
};

// ─── Content ─────────────────────────────────────────
export const contentAPI = {
  list: (params) => api.get('/content/', { params }),
  get: (id) => api.get(`/content/${id}`),
  create: (data) => api.post('/content/', data),
  interact: (id, data) => api.post(`/content/${id}/interact`, { content_id: id, ...data }),
  getFeed: (params) => api.get('/content/feed/personalized/', { params }),
  search: (params) => api.get('/content/search/', { params }),
  saved: (params) => api.get('/content/saved', { params }),
  listComments: (id, params) => api.get(`/content/${id}/comments`, { params }),
  addComment: (id, data) => api.post(`/content/${id}/comments`, data),
};

// ─── Users ───────────────────────────────────────────
export const usersAPI = {
  getProfile: (id) => api.get(`/users/${id}`),
  updateProfile: (data) => api.put('/users/profile/', data),
  follow: (id) => api.post(`/users/${id}/follow`),
  unfollow: (id) => api.delete(`/users/${id}/follow`),
  followers: (id, limit = 50) => api.get(`/users/${id}/followers`, { params: { limit } }),
  following: (id, limit = 50) => api.get(`/users/${id}/following`, { params: { limit } }),
  earnIQ: (data) => api.post('/users/iq/earn/', data),
  leaderboard: (limit) => api.get('/users/leaderboard/', { params: { limit } }),
};

// ─── Discussions ─────────────────────────────────────
export const discussionsAPI = {
  list: (params) => api.get('/discussions/', { params }),
  get: (id) => api.get(`/discussions/${id}`),
  create: (data) => api.post('/discussions/', data),
  listComments: (id) => api.get(`/discussions/${id}/comments`),
  addComment: (id, data) => api.post(`/discussions/${id}/comments`, data),
  aiChat: (data) => api.post('/discussions/ai/chat', data),
  getUserHistory: (userId) => api.get(`/discussions/user/${userId}/history`),
};

// ─── Chat ────────────────────────────────────────────
export const chatAPI = {
  listRooms: () => api.get('/chat/rooms/'),
  createRoom: (data) => api.post('/chat/rooms/', data),
  deleteRoom: (roomId) => api.delete(`/chat/rooms/${roomId}`),
  listMessages: (roomId, limit) => api.get(`/chat/messages/${roomId}`, { params: { limit } }),
  sendMessage: (data) => api.post('/chat/messages/', data),
};

// ─── Pipeline (AI Agents) ────────────────────────────
export const pipelineAPI = {
  status: () => api.get('/pipeline/status/'),
  run: (data) => api.post('/pipeline/run/', data || {}),
  getRunStatus: (runId) => api.get(`/pipeline/run/${runId}`),
  triggerAgent: (data) => api.post('/pipeline/agent/', data),
  todaysDomains: () => api.get('/pipeline/domains/today/'),
};

// ─── Quiz (AI-Generated) ────────────────────────────
export const quizAPI = {
  generate: (params) => api.get('/quiz/generate', { params }),
};

// ─── WebSocket ───────────────────────────────────────
export const getWebSocketURL = (token) => {
  const wsBase = API_BASE_URL.replace('http', 'ws');
  return `${wsBase}/ws/${token}`;
};

export default api;
