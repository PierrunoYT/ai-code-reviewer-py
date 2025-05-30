#!/usr/bin/env node

import dotenv from 'dotenv';
import { AIReviewer } from './src/ai-reviewer.js';
import chalk from 'chalk';

// Load environment variables
dotenv.config();

const testDiff = `
diff --git a/test.js b/test.js
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/test.js
@@ -0,0 +1,10 @@
+function getUserData(id) {
+  // TODO: Add input validation
+  const query = "SELECT * FROM users WHERE id = " + id;
+  return database.query(query);
+}
+
+const password = "admin123";
+
+app.get('/api/user/:id', (req, res) => {
+  res.json(getUserData(req.params.id));
+});
`;

const testCommit = {
  hash: 'abc1234',
  message: 'Add user data endpoint',
  author: 'Test User <test@example.com>',
  date: new Date().toISOString()
};

const configs = {
  'Claude 4 Sonnet': {
    aiProvider: 'anthropic',
    model: 'claude-sonnet-4-20250514',
    apiKey: process.env.ANTHROPIC_API_KEY,
    maxTokens: 4000,
    enableWebSearch: true,
    enableExtendedThinking: true,
    enableCitations: true
  },
  'Claude 4 Opus': {
    aiProvider: 'anthropic',
    model: 'claude-opus-4-20250514',
    apiKey: process.env.ANTHROPIC_API_KEY,
    maxTokens: 8000,
    enableExtendedThinking: true,
    enableCitations: true
  },
  'Claude 3.7 Sonnet': {
    aiProvider: 'anthropic',
    model: 'claude-3-7-sonnet-20250219',
    apiKey: process.env.ANTHROPIC_API_KEY,
    maxTokens: 4000,
    enableWebSearch: true,
    enableCitations: true,
    enableExtendedThinking: true
  },
  'OpenAI GPT-4o': {
    aiProvider: 'openai',
    model: 'gpt-4o',
    apiKey: process.env.OPENAI_API_KEY,
    maxTokens: 4000,
    enableWebSearch: false // OpenAI doesn't support the same web search tool
  },
  'Gemini 2.5 Pro': {
    aiProvider: 'google',
    model: 'gemini-2.5-pro-preview-05-06',
    apiKey: process.env.GOOGLE_API_KEY,
    maxTokens: 4000,
    enableWebSearch: false, // Google might not support web search in the same way
    enableExtendedThinking: true
  },
  'Gemini 2.5 Flash': {
    aiProvider: 'google',
    model: 'gemini-2.5-flash-preview-05-20',
    apiKey: process.env.GOOGLE_API_KEY,
    maxTokens: 4000,
    enableWebSearch: false,
    enableExtendedThinking: true
  }
};

async function testProvider(name, config) {
  console.log(chalk.blue(`\n🧪 Testing ${name}...`));
  
  if (!config.apiKey) {
    console.log(chalk.yellow(`⚠️  No API key found for ${name}. Skipping.`));
    return;
  }
  
  try {
    const aiReviewer = new AIReviewer(config);
    const review = await aiReviewer.reviewCode(testDiff, testCommit);
    
    console.log(chalk.green(`✅ ${name} - SUCCESS`));
    console.log(chalk.gray(`   Score: ${review.score}/10, Confidence: ${review.confidence}/10`));
    console.log(chalk.gray(`   Issues found: ${review.issues?.length || 0}`));
    
    return true;
  } catch (error) {
    console.log(chalk.red(`❌ ${name} - FAILED`));
    console.log(chalk.red(`   Error: ${error.message}`));

    if (error.response) {
      console.log(chalk.red(`   Status: ${error.response.status}`));
      console.log(chalk.red(`   Response: ${JSON.stringify(error.response.data, null, 2)}`));
    }

    return false;
  }
}

async function main() {
  console.log(chalk.blue('🚀 Testing all AI providers...\n'));
  
  const results = {};
  
  for (const [name, config] of Object.entries(configs)) {
    results[name] = await testProvider(name, config);
    
    // Add delay between tests to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  console.log(chalk.blue('\n📊 Test Results Summary:'));
  console.log('─'.repeat(50));
  
  for (const [name, success] of Object.entries(results)) {
    const status = success ? chalk.green('✅ PASS') : chalk.red('❌ FAIL');
    console.log(`${status} ${name}`);
  }
  
  const passCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;
  
  console.log(chalk.blue(`\n🎯 Overall: ${passCount}/${totalCount} providers working`));
}

main().catch(console.error);
