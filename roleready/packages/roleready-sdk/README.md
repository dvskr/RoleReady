# RoleReady JavaScript SDK

A lightweight JavaScript SDK for integrating RoleReady's resume analysis capabilities into your applications, ATS systems, and automation tools.

## Installation

### npm
```bash
npm install @roleready/sdk
```

### CDN
```html
<script src="https://cdn.roleready.app/sdk/latest/roleready-sdk.js"></script>
```

### Direct Download
Download the latest version from [GitHub Releases](https://github.com/roleready/roleready-sdk-js/releases).

## Quick Start

### 1. Initialize the SDK

```javascript
import { RoleReadySDK } from '@roleready/sdk';

const sdk = new RoleReadySDK('your-api-key-here');
```

### 2. Parse a Resume

```javascript
const resumeText = `
John Doe
Software Engineer
5 years of experience in Python and JavaScript
Worked at TechCorp and StartupXYZ
`;

const result = await sdk.parseResume(resumeText);
console.log(result.sections);
// Output: { personal_info: "John Doe, Software Engineer", experience: [...], ... }
```

### 3. Analyze Resume Match

```javascript
const jobDescription = `
We're looking for a Software Engineer with Python experience.
Must have 3+ years in web development.
`;

const analysis = await sdk.analyzeResume(resumeText, jobDescription);
console.log(`Match Score: ${Math.round(analysis.overall_score * 100)}%`);
console.log(`Matched Skills: ${analysis.matched_skills.join(', ')}`);
```

## API Reference

### Constructor

```javascript
const sdk = new RoleReadySDK(apiKey, baseUrl?)
```

- `apiKey` (string): Your RoleReady API key
- `baseUrl` (string, optional): API base URL (defaults to `https://api.roleready.app`)

### Methods

#### `parseResume(text, format?)`

Parse resume text into structured sections.

**Parameters:**
- `text` (string): Resume text to parse
- `format` (string): Output format - `'text'` or `'json'` (default: `'text'`)

**Returns:** `Promise<ParseResponse>`

```javascript
const result = await sdk.parseResume(resumeText);
```

#### `parseResumeFile(file, format?)`

Parse resume from uploaded file (PDF, DOCX, TXT).

**Parameters:**
- `file` (File): Resume file object
- `format` (string): Output format - `'text'` or `'json'` (default: `'text'`)

**Returns:** `Promise<ParseResponse>`

```javascript
const fileInput = document.getElementById('resume-file');
const result = await sdk.parseResumeFile(fileInput.files[0]);
```

#### `analyzeResume(resumeText, jobDescription, mode?)`

Analyze how well a resume matches a job description.

**Parameters:**
- `resumeText` (string): Resume text
- `jobDescription` (string): Job description text
- `mode` (string): Analysis mode - `'semantic'`, `'keyword'`, or `'hybrid'` (default: `'semantic'`)

**Returns:** `Promise<AlignResponse>`

```javascript
const analysis = await sdk.analyzeResume(resumeText, jobDescription, 'semantic');
```

#### `rewriteResume(resumeText, section, jobDescription?, style?)`

Rewrite a specific section of a resume.

**Parameters:**
- `resumeText` (string): Resume text
- `section` (string): Section to rewrite (e.g., `'summary'`, `'experience'`)
- `jobDescription` (string, optional): Job description for context
- `style` (string): Writing style - `'professional'`, `'technical'`, or `'creative'` (default: `'professional'`)

**Returns:** `Promise<RewriteResponse>`

```javascript
const rewrite = await sdk.rewriteResume(resumeText, 'summary', jobDescription, 'professional');
```

#### `getUsageStats()`

Get API usage statistics for your account.

**Returns:** `Promise<UsageStats>`

```javascript
const stats = await sdk.getUsageStats();
console.log(`Requests this month: ${stats.current_month_usage.total_requests}`);
```

#### `healthCheck()`

Check API health status.

**Returns:** `Promise<HealthResponse>`

```javascript
const health = await sdk.healthCheck();
console.log(`API Status: ${health.status}`);
```

## Utility Functions

The SDK includes utility functions for common tasks:

```javascript
import { RoleReadyUtils } from '@roleready/sdk';

// Extract skills from resume text
const skills = RoleReadyUtils.extractSkills(resumeText);

// Calculate keyword match score
const score = RoleReadyUtils.calculateKeywordScore(resumeText, jobDescription);

// Format API response for display
const formatted = RoleReadyUtils.formatResponse(analysis);
```

## Error Handling

The SDK throws descriptive errors for common issues:

```javascript
try {
  const result = await sdk.parseResume(resumeText);
} catch (error) {
  if (error.message.includes('API key')) {
    console.error('Invalid API key');
  } else if (error.message.includes('Network error')) {
    console.error('Connection failed');
  } else {
    console.error('API error:', error.message);
  }
}
```

## Browser Support

The SDK works in all modern browsers that support:
- ES6 Promises
- Fetch API
- ES6 Classes

For older browsers, use a polyfill for fetch:

```html
<script src="https://cdn.jsdelivr.net/npm/whatwg-fetch@3.6.2/dist/fetch.umd.js"></script>
```

## Node.js Usage

The SDK also works in Node.js environments:

```javascript
const { RoleReadySDK } = require('@roleready/sdk');

const sdk = new RoleReadySDK('your-api-key');
const result = await sdk.parseResume(resumeText);
```

## Examples

### ATS Integration

```javascript
// Check resume against job posting
async function evaluateCandidate(resumeFile, jobDescription) {
  const sdk = new RoleReadySDK(process.env.ROLEREADY_API_KEY);
  
  try {
    // Parse resume
    const parsed = await sdk.parseResumeFile(resumeFile);
    
    // Analyze match
    const analysis = await sdk.analyzeResume(
      JSON.stringify(parsed.sections), 
      jobDescription
    );
    
    return {
      score: Math.round(analysis.overall_score * 100),
      matchedSkills: analysis.matched_skills,
      missingSkills: analysis.missing_skills,
      suggestions: analysis.suggestions
    };
  } catch (error) {
    console.error('Evaluation failed:', error.message);
    return null;
  }
}
```

### Zapier Integration

```javascript
// Zapier Code step example
const sdk = new RoleReadySDK(inputData.apiKey);

const analysis = await sdk.analyzeResume(
  inputData.resumeText,
  inputData.jobDescription
);

output = {
  matchScore: Math.round(analysis.overall_score * 100),
  matchedSkills: analysis.matched_skills.join(', '),
  missingSkills: analysis.missing_skills.join(', '),
  suggestions: analysis.suggestions.join('; ')
};
```

### Resume Optimization Tool

```javascript
async function optimizeResume(resumeText, jobDescription) {
  const sdk = new RoleReadySDK('your-api-key');
  
  // Analyze current match
  const analysis = await sdk.analyzeResume(resumeText, jobDescription);
  
  if (analysis.overall_score < 0.7) {
    // Rewrite summary for better match
    const improvedSummary = await sdk.rewriteResume(
      resumeText, 
      'summary', 
      jobDescription
    );
    
    return {
      originalScore: analysis.overall_score,
      improvedText: improvedSummary.improved_text,
      improvements: improvedSummary.improvements
    };
  }
  
  return { score: analysis.overall_score, optimized: false };
}
```

## Rate Limits

The SDK automatically handles rate limiting. If you hit rate limits, the API will return a `429 Too Many Requests` status code.

## Support

- Documentation: [https://docs.roleready.app](https://docs.roleready.app)
- API Reference: [https://docs.roleready.app/api](https://docs.roleready.app/api)
- Support: [support@roleready.app](mailto:support@roleready.app)
- GitHub Issues: [https://github.com/roleready/roleready-sdk-js/issues](https://github.com/roleready/roleready-sdk-js/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.
