/**
 * RoleReady JavaScript SDK
 * 
 * A lightweight SDK for integrating RoleReady's resume analysis capabilities
 * into external applications, ATS systems, and automation tools.
 */

class RoleReadySDK {
  constructor(apiKey, baseUrl = 'https://api.roleready.app') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Make an authenticated request to the RoleReady API
   */
  async _makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    const requestOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, requestOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorData.detail || 'Unknown error'}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to RoleReady API. Please check your internet connection.');
      }
      throw error;
    }
  }

  /**
   * Parse resume text into structured sections
   * @param {string} text - The resume text to parse
   * @param {string} format - Output format ('text' or 'json')
   * @returns {Promise<Object>} Parsed resume data
   */
  async parseResume(text, format = 'text') {
    if (!text || typeof text !== 'string') {
      throw new Error('Resume text is required and must be a string');
    }

    return await this._makeRequest('/v1/parse', {
      method: 'POST',
      body: JSON.stringify({
        text: text,
        format: format
      })
    });
  }

  /**
   * Parse resume from file
   * @param {File} file - The resume file (PDF, DOCX, TXT)
   * @param {string} format - Output format ('text' or 'json')
   * @returns {Promise<Object>} Parsed resume data
   */
  async parseResumeFile(file, format = 'text') {
    if (!file || !(file instanceof File)) {
      throw new Error('File is required and must be a File object');
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);

    return await this._makeRequest('/v1/parse/file', {
      method: 'POST',
      headers: {
        // Remove Content-Type header to let browser set it with boundary
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: formData
    });
  }

  /**
   * Analyze how well a resume matches a job description
   * @param {string} resumeText - The resume text
   * @param {string} jobDescription - The job description text
   * @param {string} mode - Analysis mode ('semantic', 'keyword', 'hybrid')
   * @returns {Promise<Object>} Alignment analysis results
   */
  async analyzeResume(resumeText, jobDescription, mode = 'semantic') {
    if (!resumeText || typeof resumeText !== 'string') {
      throw new Error('Resume text is required and must be a string');
    }
    if (!jobDescription || typeof jobDescription !== 'string') {
      throw new Error('Job description is required and must be a string');
    }

    return await this._makeRequest('/v1/align', {
      method: 'POST',
      body: JSON.stringify({
        resume_text: resumeText,
        job_description: jobDescription,
        mode: mode
      })
    });
  }

  /**
   * Rewrite a specific section of a resume
   * @param {string} resumeText - The resume text
   * @param {string} section - The section to rewrite ('summary', 'experience', etc.)
   * @param {string} jobDescription - Optional job description for context
   * @param {string} style - Writing style ('professional', 'technical', 'creative')
   * @returns {Promise<Object>} Rewrite results
   */
  async rewriteResume(resumeText, section, jobDescription = null, style = 'professional') {
    if (!resumeText || typeof resumeText !== 'string') {
      throw new Error('Resume text is required and must be a string');
    }
    if (!section || typeof section !== 'string') {
      throw new Error('Section is required and must be a string');
    }

    return await this._makeRequest('/v1/rewrite', {
      method: 'POST',
      body: JSON.stringify({
        resume_text: resumeText,
        section: section,
        job_description: jobDescription,
        style: style
      })
    });
  }

  /**
   * Get API usage statistics
   * @returns {Promise<Object>} Usage statistics
   */
  async getUsageStats() {
    return await this._makeRequest('/v1/usage');
  }

  /**
   * Check API health
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    return await this._makeRequest('/v1/health');
  }
}

/**
 * Utility functions for common use cases
 */
const RoleReadyUtils = {
  /**
   * Extract skills from resume text using simple keyword matching
   * @param {string} text - Resume text
   * @returns {Array<string>} List of detected skills
   */
  extractSkills(text) {
    const commonSkills = [
      'JavaScript', 'Python', 'Java', 'React', 'Node.js', 'SQL', 'AWS', 'Docker',
      'Git', 'HTML', 'CSS', 'TypeScript', 'Angular', 'Vue.js', 'MongoDB',
      'PostgreSQL', 'Redis', 'Kubernetes', 'Terraform', 'Jenkins', 'CI/CD',
      'Machine Learning', 'AI', 'Data Analysis', 'Project Management',
      'Agile', 'Scrum', 'Leadership', 'Communication', 'Problem Solving'
    ];

    const detectedSkills = [];
    const lowerText = text.toLowerCase();

    commonSkills.forEach(skill => {
      if (lowerText.includes(skill.toLowerCase())) {
        detectedSkills.push(skill);
      }
    });

    return [...new Set(detectedSkills)]; // Remove duplicates
  },

  /**
   * Calculate a simple keyword-based match score
   * @param {string} resumeText - Resume text
   * @param {string} jobDescription - Job description text
   * @returns {number} Match score between 0 and 1
   */
  calculateKeywordScore(resumeText, jobDescription) {
    const resumeWords = new Set(resumeText.toLowerCase().split(/\W+/));
    const jobWords = new Set(jobDescription.toLowerCase().split(/\W+/));
    
    const commonWords = new Set([...resumeWords].filter(word => jobWords.has(word)));
    
    return jobWords.size > 0 ? commonWords.size / jobWords.size : 0;
  },

  /**
   * Format API response for display
   * @param {Object} response - API response object
   * @returns {string} Formatted string
   */
  formatResponse(response) {
    if (response.overall_score !== undefined) {
      return `Match Score: ${Math.round(response.overall_score * 100)}%\n` +
             `Matched Skills: ${response.matched_skills?.join(', ') || 'None'}\n` +
             `Missing Skills: ${response.missing_skills?.join(', ') || 'None'}`;
    }
    
    if (response.sections) {
      return `Parsed Resume Sections:\n` +
             Object.entries(response.sections)
               .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
               .join('\n');
    }
    
    return JSON.stringify(response, null, 2);
  }
};

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  // CommonJS
  module.exports = { RoleReadySDK, RoleReadyUtils };
} else if (typeof define === 'function' && define.amd) {
  // AMD
  define([], function() {
    return { RoleReadySDK, RoleReadyUtils };
  });
} else {
  // Browser global
  window.RoleReadySDK = RoleReadySDK;
  window.RoleReadyUtils = RoleReadyUtils;
}
