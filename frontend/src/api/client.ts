// API client for Dead Link Crawler backend

const API_BASE_URL = '/api';

export interface Config {
  id: string;
  name: string;
  start_url: string;
  timeout?: number;
  delay?: number;
  max_depth?: number | null;
  output_dir?: string;
  show_skipped_links?: boolean;
  whitelist_codes?: number[];
  domain_rules?: Record<string, {
    allowed_codes: number[];
    description: string;
    ignore_timeouts?: boolean;
  }>;
}

export interface Job {
  id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  config: Config;
  config_id?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  report_path?: string;
  error?: string;
  stats: {
    pages_crawled: number;
    links_checked: number;
    errors_found: number;
  };
}

export interface Report {
  filename: string;
  size: number;
  created_at: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Config endpoints
  async listConfigs(): Promise<Config[]> {
    return this.request<Config[]>('/configs');
  }

  async getConfig(id: string): Promise<Config> {
    return this.request<Config>(`/configs/${id}`);
  }

  async createConfig(config: Omit<Config, 'id'> & { id: string }): Promise<Config> {
    return this.request<Config>('/configs', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async updateConfig(id: string, config: Partial<Config>): Promise<Config> {
    return this.request<Config>(`/configs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async deleteConfig(id: string): Promise<void> {
    await this.request<void>(`/configs/${id}`, {
      method: 'DELETE',
    });
  }

  // Crawl endpoints
  async startCrawl(params: { configId?: string; config?: Config }): Promise<{ jobId: string }> {
    return this.request<{ jobId: string }>('/crawl', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Job endpoints
  async listJobs(limit?: number): Promise<Job[]> {
    const query = limit ? `?limit=${limit}` : '';
    return this.request<Job[]>(`/jobs${query}`);
  }

  async getJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}`);
  }

  async cancelJob(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/jobs/${id}/cancel`, {
      method: 'POST',
    });
  }

  // Report endpoints
  async listReports(): Promise<Report[]> {
    return this.request<Report[]>('/reports');
  }

  getReportDownloadUrl(filename: string): string {
    return `${this.baseUrl}/reports/${filename}`;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

