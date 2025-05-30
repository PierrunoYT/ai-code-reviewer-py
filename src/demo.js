#!/usr/bin/env node

import { ReviewerApp } from './index.js';
import chalk from 'chalk';

// Demo script to showcase the enhanced AI PR Reviewer features
async function runDemo() {
  console.log(chalk.blue.bold('🚀 AI PR Reviewer - Enhanced Features Demo\n'));

  // Configuration showcasing latest features
  const enhancedConfig = {
    aiProvider: 'anthropic',
    model: 'claude-sonnet-4-20250514',
    maxTokens: 64000,
    enableWebSearch: true,
    enableExtendedThinking: true,
    enableCitations: true,
    enableBatchProcessing: true,
    retryAttempts: 3,
    batchSize: 3,
    apiKey: process.env.AI_API_KEY,
    reviewCriteria: [
      'code quality',
      'security vulnerabilities',
      'performance issues',
      'naming conventions',
      'code complexity',
      'test coverage',
      'documentation',
      'accessibility',
      'dependency security'
    ]
  };

  console.log(chalk.green('✨ Enhanced Configuration:'));
  console.log(chalk.gray('  • Provider: Anthropic Claude 4 Sonnet (Latest)'));
  console.log(chalk.gray('  • Alternative Models: Claude 3.7 Sonnet, Gemini 2.5 Pro/Flash'));
  console.log(chalk.gray('  • Web Search: Enabled (Real-time best practices)'));
  console.log(chalk.gray('  • Extended Thinking: Enabled (Deeper analysis)'));
  console.log(chalk.gray('  • Citations: Enabled (Source attribution)'));
  console.log(chalk.gray('  • Batch Processing: Enabled (Faster reviews)'));
  console.log(chalk.gray('  • Enhanced Criteria: Security, Accessibility, Dependencies\n'));

  if (!enhancedConfig.apiKey) {
    console.log(chalk.red('❌ No API key found. Set AI_API_KEY environment variable.'));
    console.log(chalk.yellow('💡 Example: export AI_API_KEY="sk-ant-..."'));
    return;
  }

  try {
    const app = new ReviewerApp(enhancedConfig);

    // Demo with sample code changes
    const sampleCommit = {
      hash: 'demo123',
      message: 'Add user authentication with password validation',
      author: 'Demo User <demo@example.com>',
      date: new Date().toISOString()
    };

    const sampleDiff = `diff --git a/auth.js b/auth.js
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/auth.js
@@ -0,0 +1,25 @@
+const bcrypt = require('bcrypt');
+const jwt = require('jsonwebtoken');
+
+function authenticateUser(username, password) {
+  // TODO: Add input validation
+  const user = getUserFromDatabase(username);
+  
+  if (user && bcrypt.compareSync(password, user.hashedPassword)) {
+    const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET || 'secret-key');
+    return { success: true, token };
+  }
+  
+  return { success: false };
+}
+
+function getUserFromDatabase(username) {
+  // Simulated database query
+  const query = \`SELECT * FROM users WHERE username = '\${username}'\`;
+  return database.query(query);
+}
+
+module.exports = {
+  authenticateUser
+};`;

    console.log(chalk.cyan('🔍 Analyzing sample authentication code...\n'));
    
    const review = await app.aiReviewer.reviewCodeWithRetry(sampleDiff, sampleCommit);
    app.displayReview(review, sampleCommit);

    console.log(chalk.green('\n🎉 Demo completed! The enhanced AI reviewer found:'));
    console.log(chalk.yellow('  • Security vulnerabilities (SQL injection, hardcoded secrets)'));
    console.log(chalk.yellow('  • Missing input validation'));
    console.log(chalk.yellow('  • Performance considerations'));
    console.log(chalk.yellow('  • Best practice recommendations'));
    
    if (review.sources && review.sources.length > 0) {
      console.log(chalk.blue('  • Citations from authoritative sources'));
    }

  } catch (error) {
    console.error(chalk.red('❌ Demo failed:'), error.message);
    console.log(chalk.yellow('💡 Make sure your API key is valid and you have internet access'));
  }
}

// Feature comparison
function showFeatureComparison() {
  console.log(chalk.blue.bold('\n📊 Feature Comparison: Before vs After\n'));
  
  const features = [
    ['AI Models', 'GPT-4, Claude 3', 'GPT-4.1, Claude 4, Claude 3.7, Gemini 2.5'],
    ['Analysis Depth', 'Basic code review', 'Extended thinking + web search'],
    ['Processing', 'Sequential only', 'Batch processing available'],
    ['Citations', 'Not available', 'Source attribution included'],
    ['Retry Logic', 'Basic error handling', 'Exponential backoff retry'],
    ['Review Criteria', '7 categories', '9 categories + accessibility'],
    ['Token Limit', '2000 tokens', '32K-128K tokens'],
    ['Configuration', 'Static config', 'Multiple provider configs (Anthropic, OpenAI, Google)']
  ];

  console.log(chalk.gray('Feature'.padEnd(20)) + chalk.gray('Before'.padEnd(25)) + chalk.gray('After'));
  console.log(chalk.gray('─'.repeat(70)));
  
  features.forEach(([feature, before, after]) => {
    console.log(
      chalk.white(feature.padEnd(20)) + 
      chalk.red(before.padEnd(25)) + 
      chalk.green(after)
    );
  });
}

// Main execution
if (import.meta.url === `file://${process.argv[1]}`) {
  showFeatureComparison();
  runDemo().catch(console.error);
}

export { runDemo, showFeatureComparison };
