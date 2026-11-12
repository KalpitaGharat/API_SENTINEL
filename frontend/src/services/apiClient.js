/**
 * API Sentinel Centralized HTTP Client
 *
 * Provides typed, resilient communication with the FastAPI backend,
 * supporting timeout safeguards, consistent error handling, response validation,
 * and zero leaked credentials.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const DEFAULT_TIMEOUT_MS = 30000;
const LONG_TIMEOUT_MS = 60000;

export class ApiError extends Error {
  constructor(message, status = null, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
    this.isNetworkError = status === null || status === 0;
  }
}

async function request(endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const url = `${BASE_URL.replace(/\/+$/, '')}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
    },
    signal: controller.signal,
  };

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    let data = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await response.json().catch(() => null);
    } else {
      const text = await response.text();
      data = text ? { message: text } : null;
    }

    if (!response.ok) {
      const errorMsg = data?.detail || data?.message || `HTTP ${response.status} ${response.statusText}`;
      throw new ApiError(errorMsg, response.status, data);
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError(`Request to ${endpoint} timed out after ${Math.round(timeoutMs / 1000)}s`, 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    // Network / connection refused / offline
    throw new ApiError(
      `Unable to reach backend at ${BASE_URL}. Ensure the FastAPI server is running on port 8000. (${err.message})`,
      0,
      err
    );
  }
}

export const apiClient = {
  baseUrl: BASE_URL,

  /** System & Health Checks */
  async getHealth() {
    return request('/health');
  },

  async getApiHealth() {
    return request('/api/health');
  },

  /** Scans */
  async createScan({ targetUrl, scanProfile = 'OWASP API Top 10 Deep Audit', userAuthorized = true, categories = ['BOLA', 'AUTH', 'HEADERS', 'CONFIG'] }) {
    return request('/api/scans', {
      method: 'POST',
      body: JSON.stringify({
        target_url: targetUrl,
        scan_profile: scanProfile,
        user_authorized: Boolean(userAuthorized),
        categories: categories,
      }),
    }, LONG_TIMEOUT_MS);
  },

  async getScans({ skip = 0, limit = 20, statusFilter = null } = {}) {
    const params = new URLSearchParams();
    if (skip) params.append('skip', skip);
    if (limit) params.append('limit', limit);
    if (statusFilter && statusFilter !== 'All') params.append('status_filter', statusFilter);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/scans${query}`);
  },

  async getScan(scanId) {
    if (!scanId) throw new ApiError('scanId is required', 400);
    return request(`/api/scans/${encodeURIComponent(scanId)}`);
  },

  async getScanFindings(scanId, { severity = null, category = null, status = null } = {}) {
    if (!scanId) throw new ApiError('scanId is required', 400);
    const params = new URLSearchParams();
    if (severity && severity !== 'All') params.append('severity', severity);
    if (category && category !== 'All') params.append('category', category);
    if (status && status !== 'All') params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/scans/${encodeURIComponent(scanId)}/findings${query}`);
  },

  /** Findings & AI Explanations */
  async getFinding(findingId) {
    if (!findingId) throw new ApiError('findingId is required', 400);
    return request(`/api/findings/${encodeURIComponent(findingId)}`);
  },

  async explainFinding(findingId, forceRefresh = false) {
    if (!findingId) throw new ApiError('findingId is required', 400);
    const query = forceRefresh ? '?force_refresh=true' : '';
    return request(`/api/findings/${encodeURIComponent(findingId)}/explain${query}`, {
      method: 'POST',
    }, LONG_TIMEOUT_MS);
  },

  async getFindingHistory(findingId) {
    if (!findingId) throw new ApiError('findingId is required', 400);
    return request(`/api/findings/${encodeURIComponent(findingId)}/history`);
  },

  async exportFindingEvidence(findingId) {
    if (!findingId) throw new ApiError('findingId is required', 400);
    return request(`/api/findings/${encodeURIComponent(findingId)}/export-evidence`);
  },

  /** Retesting & Verification Probing */
  async retestScan(scanId, findingId = null) {
    if (!scanId) throw new ApiError('scanId is required', 400);
    const payload = {};
    if (findingId) {
      payload.finding_id = findingId;
    }
    return request(`/api/scans/${encodeURIComponent(scanId)}/retest`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, LONG_TIMEOUT_MS);
  },

  /** Reports */
  async getScanReport(scanId) {
    if (!scanId) throw new ApiError('scanId is required', 400);
    return request(`/api/scans/${encodeURIComponent(scanId)}/report`);
  },

  /** Target Onboarding & OpenAPI Discovery */
  async getTargets({ environment = null, search = null, skip = 0, limit = 50 } = {}) {
    const params = new URLSearchParams();
    if (environment && environment !== 'All') params.append('environment', environment);
    if (search) params.append('search', search);
    if (skip) params.append('skip', skip);
    if (limit) params.append('limit', limit);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/targets${query}`);
  },

  async getTarget(targetId) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}`);
  },

  async createTarget(payload) {
    return request('/api/targets', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateTarget(targetId, payload) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async deleteTarget(targetId) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}`, {
      method: 'DELETE',
    });
  },

  async previewOpenApiSpec(specContent) {
    return request('/api/targets/preview-spec', {
      method: 'POST',
      body: JSON.stringify({ spec_content: specContent }),
    });
  },

  async importOpenApiSpec(targetId, { spec_content = null, spec_url = null }) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/import-spec`, {
      method: 'POST',
      body: JSON.stringify({ spec_content, spec_url }),
    }, LONG_TIMEOUT_MS);
  },

  async getTargetEndpoints(targetId, { method = null, sensitive_only = null, selected_only = null, search = null, skip = 0, limit = 200 } = {}) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    const params = new URLSearchParams();
    if (method && method !== 'ALL') params.append('method', method);
    if (sensitive_only !== null && sensitive_only !== undefined) params.append('sensitive_only', sensitive_only);
    if (selected_only !== null && selected_only !== undefined) params.append('selected_only', selected_only);
    if (search) params.append('search', search);
    if (skip) params.append('skip', skip);
    if (limit) params.append('limit', limit);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/targets/${encodeURIComponent(targetId)}/endpoints${query}`);
  },

  async updateEndpointSelection(targetId, { endpoint_ids = null, select_all = null, deselect_all = null, sensitive_only = null }) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/endpoints/select`, {
      method: 'POST',
      body: JSON.stringify({ endpoint_ids, select_all, deselect_all, sensitive_only }),
    });
  },

  async saveAuthProfile(targetId, payload) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/auth-profiles`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getAuthProfiles(targetId) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/auth-profiles`);
  },

  async validateTargetConnectivity(targetId) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/validate`, {
      method: 'POST',
    });
  },

  async launchTargetScan(targetId, payload) {
    if (!targetId) throw new ApiError('targetId is required', 400);
    return request(`/api/targets/${encodeURIComponent(targetId)}/scan`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, LONG_TIMEOUT_MS);
  },
};

export default apiClient;
