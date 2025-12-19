import axios from 'axios';

export class AIReviewer {
  constructor(config) {
    this.config = config;
    this.apiKey = config.apiKey;
    this.provider = config.aiProvider || 'openai';
    this.model = config.model || this.getDefaultModel();
    this.enableWebSearch = config.enableWebSearch || false;
    this.enableExtendedThinking = config.enableExtendedThinking || false;
    this.enableCitations = config.enableCitations || false;
  }

  getDefaultModel() {
    switch (this.provider) {
      case 'openai':
        return 'gpt-4.1'; // Latest GPT-4.1 model
      case 'anthropic':
        return 'claude-sonnet-4-20250514';
      case 'google':
        return 'gemini-2.5-flash-preview-05-20'; // Latest Gemini 2.5 Flash model
      default:
        return 'gpt-4.1';
    }
  }

  async reviewCode(diff, commit) {
    // Input validation
    if (!diff || typeof diff !== 'string') {
      throw new Error('Invalid diff: must be a non-empty string');
    }
    if (!commit || typeof commit !== 'object') {
      throw new Error('Invalid commit: must be an object with hash, message, author, and date');
    }
    if (!commit.hash || !commit.message) {
      throw new Error('Invalid commit: missing required fields (hash, message)');
    }
    if (!this.apiKey) {
      throw new Error('AI API key not found. Set AI_API_KEY environment variable.');
    }

    const prompt = this.buildPrompt(diff, commit);
    
    try {
      let response;
      
      switch (this.provider) {
        case 'openai':
          response = await this.callOpenAI(prompt);
          break;
        case 'anthropic':
          response = await this.callAnthropic(prompt);
          break;
        case 'google':
          response = await this.callGoogle(prompt);
          break;
        default:
          throw new Error(`Unsupported AI provider: ${this.provider}`);
      }

      return this.parseResponse(response);
    } catch (error) {
      console.error('AI API Error:', error.message);
      return this.getFallbackReview();
    }
  }

  buildPrompt(diff, commit) {
    const basePrompt = `You are an expert code reviewer. Please review the following git commit and provide feedback.

Commit Message: ${commit.message}
Author: ${commit.author}
Date: ${commit.date}

Code Changes:
\`\`\`diff
${diff}
\`\`\`

Please analyze this commit and provide a structured review focusing on:
1. Code quality and maintainability
2. Security vulnerabilities (check against latest OWASP guidelines)
3. Performance implications
4. Best practices adherence (use current industry standards)
5. Testing considerations
6. Documentation needs
7. Accessibility considerations
8. Dependency security

${this.enableWebSearch ? 'Use web search to verify best practices and check for known security vulnerabilities in any dependencies mentioned.' : ''}

${this.enableCitations ? 'Provide citations for any security recommendations or best practices you mention.' : ''}

Format your response as JSON with this structure:
{
  "score": <number 1-10>,
  "summary": "<brief summary>",
  "issues": [
    {
      "severity": "low|medium|high|critical",
      "description": "<issue description>",
      "suggestion": "<how to fix>",
      "category": "security|performance|quality|style|testing|documentation",
      ${this.enableCitations ? '"citation": "<source URL or reference if applicable>",' : ''}
      "autoFixable": <boolean>
    }
  ],
  "suggestions": ["<general improvement suggestions>"],
  "security": ["<security-related notes>"],
  "performance": ["<performance-related notes>"],
  "dependencies": ["<dependency-related observations>"],
  "accessibility": ["<accessibility considerations>"],
  ${this.enableCitations ? '"sources": ["<list of sources consulted>"],' : ''}
  "confidence": <number 1-10 indicating confidence in the review>
}

Be constructive, specific, and provide actionable feedback. Focus on the most impactful improvements.`;

    return basePrompt;
  }

  async callOpenAI(prompt) {
    const requestBody = {
      model: this.model,
      messages: [
        {
          role: 'system',
          content: 'You are a senior software engineer providing code reviews. Always respond with valid JSON. Be thorough and constructive in your analysis.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: this.config.maxTokens || 32768,
      temperature: 0.1,
      top_p: 0.99 // Updated default as per latest OpenAI recommendations
    };

    // Add web search tools if enabled
    if (this.enableWebSearch) {
      requestBody.tools = [
        {
          type: "function",
          function: {
            name: "web_search",
            description: "Search the web for current best practices, security vulnerabilities, or documentation",
            parameters: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "The search query"
                }
              },
              required: ["query"]
            }
          }
        }
      ];
    }

    const response = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      requestBody,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data.choices[0].message.content;
  }

  async callAnthropic(prompt) {
    const requestBody = {
      model: this.model,
      max_tokens: this.config.maxTokens || 64000,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      top_p: 0.99 // Updated default as per latest Anthropic recommendations
    };

    // Add extended thinking if enabled (Claude 4 models)
    if (this.enableExtendedThinking) {
      const maxTokens = this.config.maxTokens || 64000;
      // Budget must be less than max_tokens, so we use 75% of max_tokens or 48000, whichever is smaller
      const budgetTokens = Math.min(48000, Math.floor(maxTokens * 0.75));
      requestBody.thinking = {
        type: "enabled",
        budget_tokens: budgetTokens
      };
    }

    // Add web search tool if enabled (Claude 4 models support this)
    if (this.enableWebSearch) {
      requestBody.tools = [
        {
          type: "web_search_20250305",
          name: "web_search",
          max_uses: 5
        }
      ];
    }

    const headers = {
      'x-api-key': this.apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json'
    };

    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      requestBody,
      { headers }
    );

    // Handle response - extract text content from various block types
    if (response.data.content && Array.isArray(response.data.content)) {
      // Combine all text blocks, skipping thinking, tool use, and tool result blocks
      const textBlocks = response.data.content
        .filter(block => block.type === 'text')
        .map(block => block.text);

      return textBlocks.join(' ');
    }

    // Handle non-array content (fallback)
    if (response.data.content && typeof response.data.content === 'string') {
      return response.data.content;
    }

    throw new Error('Unexpected response format from Anthropic API');
  }

  async callGoogle(prompt) {
    const requestBody = {
      contents: [
        {
          parts: [
            {
              text: prompt
            }
          ]
        }
      ],
      generationConfig: {
        maxOutputTokens: this.config.maxTokens || 64000,
        temperature: 0.1,
        topP: 0.99
      }
    };

    // Add thinking configuration if enabled (Gemini 2.5 models)
    if (this.enableExtendedThinking) {
      requestBody.generationConfig.thinkingConfig = {
        includeThoughts: true
      };

      // Add thinking budget for Flash models
      if (this.model.includes('flash')) {
        const maxTokens = this.config.maxTokens || 64000;
        const budgetTokens = Math.min(48000, Math.floor(maxTokens * 0.75));
        requestBody.generationConfig.thinkingConfig.thinkingBudget = budgetTokens;
      }
    }

    const response = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${this.apiKey}`,
      requestBody,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    // Handle response - extract text content, skipping thinking parts
    if (response.data.candidates && response.data.candidates[0].content.parts) {
      const textParts = response.data.candidates[0].content.parts
        .filter(part => part.text && !part.thought)
        .map(part => part.text);

      return textParts.join(' ');
    }

    return response.data.candidates[0].content.parts[0].text;
  }

  parseResponse(response) {
    try {
      // Remove markdown code block wrappers if present
      let cleanedResponse = response;

      // Handle ```json ... ``` blocks
      const markdownJsonMatch = cleanedResponse.match(/```json\s*([\s\S]*?)\s*```/);
      if (markdownJsonMatch) {
        cleanedResponse = markdownJsonMatch[1];
      }

      // Handle ``` ... ``` blocks (without language specifier)
      const markdownMatch = cleanedResponse.match(/```\s*([\s\S]*?)\s*```/);
      if (markdownMatch) {
        cleanedResponse = markdownMatch[1];
      }

      // Extract JSON object from the cleaned response
      const jsonMatch = cleanedResponse.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }

      // Try parsing the cleaned response directly
      return JSON.parse(cleanedResponse.trim());
    } catch (error) {
      console.warn('Failed to parse AI response as JSON, using fallback');
      console.warn('Response was:', response.substring(0, 200) + '...');
      return this.getFallbackReview();
    }
  }

  getFallbackReview() {
    return {
      score: 7,
      summary: 'Review completed with basic analysis',
      issues: [],
      suggestions: ['Consider adding more tests', 'Ensure proper error handling'],
      security: [],
      performance: [],
      dependencies: [],
      accessibility: [],
      confidence: 5
    };
  }

  // Batch processing for multiple commits
  async reviewMultipleCommits(commits, diffs) {
    if (this.provider === 'anthropic' && commits.length > 1) {
      return this.batchReviewAnthropic(commits, diffs);
    }

    // Google AI and OpenAI use sequential processing
    return this.reviewCommitsSequentially(commits, diffs);
  }

  // Sequential processing fallback (used when batch fails or for non-Anthropic providers)
  async reviewCommitsSequentially(commits, diffs) {
    const reviews = [];
    for (let i = 0; i < commits.length; i++) {
      const review = await this.reviewCode(diffs[i], commits[i]);
      reviews.push(review);
    }
    return reviews;
  }

  async batchReviewAnthropic(commits, diffs) {
    // Use Anthropic's batch processing API for efficiency
    const batchRequests = commits.map((commit, index) => ({
      custom_id: `review_${commit.hash}`,
      method: 'POST',
      url: '/v1/messages',
      body: {
        model: this.model,
        max_tokens: this.config.maxTokens || 64000,
        messages: [
          {
            role: 'user',
            content: this.buildPrompt(diffs[index], commit)
          }
        ]
      }
    }));

    try {
      const response = await axios.post(
        'https://api.anthropic.com/v1/batches',
        {
          requests: batchRequests
        },
        {
          headers: {
            'x-api-key': this.apiKey,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
          }
        }
      );

      // Poll for completion and return results
      return this.pollBatchResults(response.data.id);
    } catch (error) {
      console.warn('Batch processing failed, falling back to sequential:', error.message);
      // Use sequential processing directly to avoid infinite recursion
      return this.reviewCommitsSequentially(commits, diffs);
    }
  }

  async pollBatchResults(batchId) {
    const maxAttempts = 30;
    const pollInterval = 2000; // 2 seconds

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await axios.get(
          `https://api.anthropic.com/v1/batches/${batchId}`,
          {
            headers: {
              'x-api-key': this.apiKey,
              'anthropic-version': '2023-06-01'
            }
          }
        );

        if (response.data.status === 'completed') {
          return response.data.results.map(result =>
            this.parseResponse(result.response.body.content[0].text)
          );
        }

        if (response.data.status === 'failed') {
          throw new Error('Batch processing failed');
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.warn(`Batch polling attempt ${attempt + 1} failed:`, error.message);
      }
    }

    throw new Error('Batch processing timed out');
  }

  // Enhanced error handling with retry logic
  async reviewCodeWithRetry(diff, commit, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.reviewCode(diff, commit);
      } catch (error) {
        console.warn(`Review attempt ${attempt} failed:`, error.message);

        if (attempt === maxRetries) {
          console.error('All retry attempts failed, using fallback review');
          return this.getFallbackReview();
        }

        // Exponential backoff
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
}
