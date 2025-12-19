import { simpleGit } from 'simple-git';

export class GitAnalyzer {
  constructor(repoPath = '.') {
    this.git = simpleGit(repoPath);
  }

  async getCommits(range = 'HEAD~1..HEAD') {
    if (!range || typeof range !== 'string' || !range.includes('..')) {
      throw new Error('Invalid commit range: must be a string in format "from..to"');
    }
    try {
      const log = await this.git.log({
        from: range.split('..')[0],
        to: range.split('..')[1] || 'HEAD',
        format: {
          hash: '%H',
          date: '%ai',
          message: '%s',
          author: '%an <%ae>',
          body: '%b'
        }
      });

      return log.all.map(commit => ({
        hash: commit.hash,
        message: commit.message,
        author: commit.author,
        date: commit.date,
        body: commit.body
      }));
    } catch (error) {
      throw new Error(`Failed to get commits: ${error.message}`);
    }
  }

  async getCommitDiff(commitHash) {
    if (!commitHash || typeof commitHash !== 'string') {
      throw new Error('Invalid commit hash: must be a non-empty string');
    }
    try {
      const fullDiff = await this.git.show([
        commitHash,
        '--pretty=format:',
        '--unified=3'
      ]);

      return fullDiff;
    } catch (error) {
      throw new Error(`Failed to get diff for commit ${commitHash}: ${error.message}`);
    }
  }

  async getChangedFiles(commitHash) {
    if (!commitHash || typeof commitHash !== 'string') {
      throw new Error('Invalid commit hash: must be a non-empty string');
    }
    try {
      const result = await this.git.show([
        '--name-only',
        '--pretty=format:',
        commitHash
      ]);

      return result.trim().split('\n').filter(file => file.length > 0);
    } catch (error) {
      throw new Error(`Failed to get changed files: ${error.message}`);
    }
  }

  async getStagedChanges() {
    try {
      const diff = await this.git.diff(['--cached']);
      return diff;
    } catch (error) {
      throw new Error(`Failed to get staged changes: ${error.message}`);
    }
  }

  async getCurrentBranch() {
    try {
      const branch = await this.git.revparse(['--abbrev-ref', 'HEAD']);
      return branch.trim();
    } catch (error) {
      throw new Error(`Failed to get current branch: ${error.message}`);
    }
  }

  async isWorkingDirectoryClean() {
    try {
      const status = await this.git.status();
      return status.files.length === 0;
    } catch (error) {
      throw new Error(`Failed to check working directory status: ${error.message}`);
    }
  }

  async getFileContent(filePath, commitHash = 'HEAD') {
    if (!filePath || typeof filePath !== 'string') {
      throw new Error('Invalid file path: must be a non-empty string');
    }
    try {
      return await this.git.show([`${commitHash}:${filePath}`]);
    } catch (error) {
      throw new Error(`Failed to get file content: ${error.message}`);
    }
  }
}
