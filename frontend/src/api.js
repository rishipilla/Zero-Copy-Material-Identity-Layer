const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  demoLogin: (password) => request('/api/auth/demo-login', {
    method: 'POST',
    body: JSON.stringify({ password }),
  }),
  health: () => request('/api/health'),

  listMaterials: (sourceSystem) =>
    request(`/api/materials${sourceSystem ? `?source_system=${sourceSystem}` : ''}`),

  importSample: () => request('/api/materials/import-sample', { method: 'POST' }),

  importCsv: (sourceSystem, file) => {
    const form = new FormData();
    form.append('source_system', sourceSystem);
    form.append('file', file);
    return request('/api/materials/import', { method: 'POST', body: form });
  },

  resetAll: () => request('/api/materials/reset', { method: 'DELETE' }),

  listMatches: (status = 'pending') => request(`/api/matches?status=${status}`),

  resolveMatch: (matchId, action, canonicalName) =>
    request(`/api/matches/${matchId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ action, canonical_name: canonicalName }),
    }),

  getGraph: () => request('/api/graph'),
  graphStatus: () => request('/api/graph/status'),

  getAnalytics: () => request('/api/analytics'),

  listIntegrations: () => request('/api/integrations'),
  integrationHealth: () => request('/api/integrations/health'),
  integrationStatus: (provider) => request(`/api/integrations/${provider}/status`),
  testIntegration: (provider) => request(`/api/integrations/${provider}/test`, { method: 'POST' }),
  syncIntegration: (provider) => request(`/api/integrations/${provider}/sync`, { method: 'POST' }),
  integrationActivity: () => request('/api/integrations/activity'),
  getMaterial: (id) => request(`/api/materials/${id}`),
  getIdentity: (id) => request(`/api/identities/${id}`),
};
