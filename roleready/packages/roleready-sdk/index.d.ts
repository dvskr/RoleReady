/**
 * TypeScript definitions for RoleReady JavaScript SDK
 */

export interface ParseResponse {
  message: string;
  sections: {
    personal_info?: string;
    summary?: string;
    experience?: string[];
    education?: string[];
    skills?: string[];
  };
  confidence?: number;
  processing_time_ms: number;
}

export interface AlignResponse {
  overall_score: number;
  section_scores: Record<string, number>;
  suggestions: string[];
  matched_skills: string[];
  missing_skills: string[];
  processing_time_ms: number;
}

export interface RewriteResponse {
  original_text: string;
  improved_text: string;
  improvements: string[];
  confidence: number;
  processing_time_ms: number;
}

export interface UsageStats {
  api_key_name: string;
  created_at: string;
  last_used_at: string | null;
  current_month_usage: {
    total_requests: number;
    successful_requests: number;
    success_rate: number;
    average_response_time_ms: number;
    endpoint_breakdown: Record<string, { count: number; success_rate: number }>;
  };
  limits: {
    requests_per_month: number;
    requests_remaining: number;
  };
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export class RoleReadySDK {
  constructor(apiKey: string, baseUrl?: string);

  /**
   * Parse resume text into structured sections
   */
  parseResume(text: string, format?: 'text' | 'json'): Promise<ParseResponse>;

  /**
   * Parse resume from file
   */
  parseResumeFile(file: File, format?: 'text' | 'json'): Promise<ParseResponse>;

  /**
   * Analyze how well a resume matches a job description
   */
  analyzeResume(resumeText: string, jobDescription: string, mode?: 'semantic' | 'keyword' | 'hybrid'): Promise<AlignResponse>;

  /**
   * Rewrite a specific section of a resume
   */
  rewriteResume(resumeText: string, section: string, jobDescription?: string | null, style?: 'professional' | 'technical' | 'creative'): Promise<RewriteResponse>;

  /**
   * Get API usage statistics
   */
  getUsageStats(): Promise<UsageStats>;

  /**
   * Check API health
   */
  healthCheck(): Promise<HealthResponse>;
}

export const RoleReadyUtils: {
  /**
   * Extract skills from resume text using simple keyword matching
   */
  extractSkills(text: string): string[];

  /**
   * Calculate a simple keyword-based match score
   */
  calculateKeywordScore(resumeText: string, jobDescription: string): number;

  /**
   * Format API response for display
   */
  formatResponse(response: any): string;
};

export { RoleReadySDK as default, RoleReadyUtils };
