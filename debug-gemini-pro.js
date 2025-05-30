#!/usr/bin/env node

import dotenv from 'dotenv';
import { AIReviewer } from './src/ai-reviewer.js';

// Load environment variables
dotenv.config();

const testDiff = `
diff --git a/test.js b/test.js
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/test.js
@@ -0,0 +1,5 @@
+function getUserData(id) {
+  const query = "SELECT * FROM users WHERE id = " + id;
+  return database.query(query);
+}
`;

const testCommit = {
  hash: 'abc1234',
  message: 'Add user data endpoint',
  author: 'Test User <test@example.com>',
  date: new Date().toISOString()
};

const config = {
  aiProvider: 'google',
  model: 'gemini-2.5-pro-preview-05-06',
  apiKey: process.env.GOOGLE_API_KEY,
  maxTokens: 8000, // Increased to see if it's a token limit issue
  enableWebSearch: false,
  enableExtendedThinking: true
};

async function debugGeminiPro() {
  console.log('🔍 Debugging Gemini 2.5 Pro response...\n');
  
  if (!config.apiKey) {
    console.log('❌ No Google API key found');
    return;
  }
  
  try {
    const aiReviewer = new AIReviewer(config);
    
    // Intercept the raw response
    const originalCallGoogle = aiReviewer.callGoogle.bind(aiReviewer);
    aiReviewer.callGoogle = async function(prompt) {
      const response = await originalCallGoogle(prompt);
      console.log('📄 FULL RAW RESPONSE:');
      console.log('─'.repeat(80));
      console.log(response);
      console.log('─'.repeat(80));
      console.log(`Response length: ${response.length} characters`);
      console.log(`Starts with: "${response.substring(0, 50)}"`);
      console.log(`Ends with: "${response.substring(response.length - 50)}"`);
      console.log('─'.repeat(80));
      
      // Test the parsing manually
      console.log('\n🧪 Testing parsing logic...');
      try {
        const parsed = aiReviewer.parseResponse(response);
        console.log('✅ Parsing successful!');
        console.log('Parsed result:', JSON.stringify(parsed, null, 2));
      } catch (error) {
        console.log('❌ Parsing failed:', error.message);
      }
      
      return response;
    };
    
    console.log('Making API call...\n');
    const review = await aiReviewer.reviewCode(testDiff, testCommit);
    
    console.log('\n📊 Final review result:');
    console.log(`Score: ${review.score}/10`);
    console.log(`Issues: ${review.issues?.length || 0}`);
    console.log(`Summary: ${review.summary}`);
    
  } catch (error) {
    console.log('❌ Error:', error.message);
    if (error.response) {
      console.log('Response status:', error.response.status);
      console.log('Response data:', JSON.stringify(error.response.data, null, 2));
    }
  }
}

debugGeminiPro().catch(console.error);
