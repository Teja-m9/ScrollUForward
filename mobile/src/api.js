import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Change this to your backend URL
// Railway hobby (production):
const API_BASE_URL = 'https://scrolluforward-production.up.railway.app';
// Local dev: const API_BASE_URL = 'http://10.108.71.53:8001';

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

// ─── 401 auto-logout (Stage 1 UX) ────────────────────
// When the JWT expires, every authed call returns 401. Without this handler
// the app silently shows blank screens (no profile stats, no followers,
// chat send fails). Now we detect 401, wipe the stored creds, and notify
// App.js so it can drop the user back to the login screen.
let _onAuthFailure = null;
export const setAuthFailureHandler = (fn) => { _onAuthFailure = fn; };

let _loggingOut = false;   // dedupe — multiple 401s shouldn't spam logout
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401 && !_loggingOut) {
      _loggingOut = true;
      try {
        await AsyncStorage.multiRemove(['auth_token', 'user_id', 'username', 'scrollu_user']);
      } catch (e) {}
      try { _onAuthFailure && _onAuthFailure(); } catch (e) {}
      // Reset the latch shortly — user might re-login while app open
      setTimeout(() => { _loggingOut = false; }, 1500);
    }
    return Promise.reject(error);
  }
);

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
  stats: (id) => api.get(`/users/${id}/stats`),
  myPosts: (id, limit = 50) => api.get(`/users/${id}/posts`, { params: { limit } }),
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
// NOTE: paths intentionally have NO trailing slash. FastAPI 307-redirects
// trailing-slash POSTs which loses the body on some Android stacks.
export const chatAPI = {
  listRooms: () => api.get('/chat/rooms'),
  createRoom: (data) => api.post('/chat/rooms', data),
  deleteRoom: (roomId) => api.delete(`/chat/rooms/${roomId}`),
  listMessages: (roomId, limit) => api.get(`/chat/messages/${roomId}`, { params: { limit } }),
  sendMessage: (data) => api.post('/chat/messages', data),
  uploadAttachment: (data) => api.post('/chat/upload', data, { timeout: 60000 }),
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

// ─── Flashcards (AI-Generated) ──────────────────────
export const flashcardAPI = {
  generate: (data) => api.post('/flashcards/generate', data),
};

// ─── Map (Real-time user positions) ─────────────────
export const mapAPI = {
  updateLocation: (data) => api.post('/map/location', data),
  clearLocation: () => api.delete('/map/location'),
  nearby: () => api.get('/map/nearby'),
  trending: () => api.get('/map/trending'),
};

// ─── Brain Fingerprint (knowledge graph) ────────────
export const brainAPI = {
  get: () => api.get('/brain/fingerprint'),
  history: (domain, limit = 30) => api.get('/brain/history', { params: { domain, limit } }),
};

// ─── Knowledge Battle (1v1 + team duels) ─────────────
export const battleAPI = {
  // Solo
  queue: (domain) => api.post('/battle/queue', { domain }, { timeout: 40000 }),
  cancelQueue: (domain) => api.post('/battle/queue/cancel', { domain }),
  state: (id) => api.get(`/battle/${id}/state`),
  answer: (id, data) => api.post(`/battle/${id}/answer`, data),
  // Team
  teamQueue: (team_id, domain) => api.post('/battle/team/queue', { team_id, domain }, { timeout: 40000 }),
  cancelTeamQueue: (team_id, domain) => api.post('/battle/team/queue/cancel', { team_id, domain }),
  teamAnswer: (id, data) => api.post(`/battle/team-answer/${id}`, data),
  // Common
  leave: (id) => api.post(`/battle/${id}/leave`),
  leaderboard: (limit = 20) => api.get('/battle/leaderboard', { params: { limit } }),
};

// ─── Teams (for team battles) ────────────────────────
export const teamAPI = {
  create: (name) => api.post('/battle/team', { name }),
  join: (code) => api.post('/battle/team/join', { code }),
  leave: (id) => api.post(`/battle/team/${id}/leave`),
  kick: (id, memberId) => api.delete(`/battle/team/${id}/members/${memberId}`),
  my: () => api.get('/battle/team/my'),
  get: (id) => api.get(`/battle/team/${id}`),
};

// ─── WebSocket ───────────────────────────────────────
export const getWebSocketURL = (token) => {
  const wsBase = API_BASE_URL.replace('http', 'ws');
  return `${wsBase}/ws/${token}`;
};

export default api;
