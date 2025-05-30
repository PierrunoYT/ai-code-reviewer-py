import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export class GitHookInstaller {
  constructor(repoPath = '.') {
    this.repoPath = repoPath;
    this.hooksPath = path.join(repoPath, '.git', 'hooks');
  }

  async installPreCommitHook() {
    const hookContent = `#!/bin/sh
# AI PR Reviewer - Pre-commit hook

echo "🔍 Running AI code review..."

# Get staged changes
if ! git diff --cached --quiet; then
  # Review staged changes
  npx ai-reviewer review --staged
  exit_code=$?
  
  if [ $exit_code -ne 0 ]; then
    echo "❌ Code review failed. Commit blocked."
    echo "💡 Fix the issues above or use 'git commit --no-verify' to bypass"
    exit 1
  fi
  
  echo "✅ Code review passed"
else
  echo "ℹ️  No staged changes to review"
fi

exit 0
`;

    const hookPath = path.join(this.hooksPath, 'pre-commit');
    await this.writeHook(hookPath, hookContent);
  }

  async installPrePushHook() {
    const hookContent = `#!/bin/sh
# AI PR Reviewer - Pre-push hook

remote="$1"
url="$2"

echo "🔍 Running AI code review before push..."

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Review commits that are about to be pushed
if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
  # Find the merge base with main/master
  base_branch="main"
  if ! git show-ref --verify --quiet refs/heads/main; then
    base_branch="master"
  fi
  
  if git show-ref --verify --quiet refs/heads/$base_branch; then
    commit_range="$base_branch..HEAD"
    echo "📝 Reviewing commits in range: $commit_range"
    
    npx ai-reviewer review "$commit_range"
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
      echo "❌ Code review failed. Push blocked."
      echo "💡 Fix the issues above or use 'git push --no-verify' to bypass"
      exit 1
    fi
    
    echo "✅ Code review passed"
  else
    echo "⚠️  Could not find base branch ($base_branch), skipping review"
  fi
else
  echo "ℹ️  Pushing to main/master branch, skipping review"
fi

exit 0
`;

    const hookPath = path.join(this.hooksPath, 'pre-push');
    await this.writeHook(hookPath, hookContent);
  }

  async writeHook(hookPath, content) {
    // Ensure hooks directory exists
    if (!fs.existsSync(this.hooksPath)) {
      throw new Error('Git hooks directory not found. Are you in a git repository?');
    }

    // Backup existing hook if it exists
    if (fs.existsSync(hookPath)) {
      const backupPath = `${hookPath}.backup`;
      fs.copyFileSync(hookPath, backupPath);
      console.log(`Backed up existing hook to ${backupPath}`);
    }

    // Write new hook
    fs.writeFileSync(hookPath, content);
    
    // Make executable (Unix systems)
    if (process.platform !== 'win32') {
      fs.chmodSync(hookPath, 0o755);
    }
  }

  async uninstallHooks() {
    const hooks = ['pre-commit', 'pre-push'];
    
    for (const hook of hooks) {
      const hookPath = path.join(this.hooksPath, hook);
      const backupPath = `${hookPath}.backup`;
      
      if (fs.existsSync(hookPath)) {
        if (fs.existsSync(backupPath)) {
          fs.copyFileSync(backupPath, hookPath);
          fs.unlinkSync(backupPath);
          console.log(`Restored ${hook} hook from backup`);
        } else {
          fs.unlinkSync(hookPath);
          console.log(`Removed ${hook} hook`);
        }
      }
    }
  }
}
