import { access, cp, rm, mkdir, readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { updateGeneratedDocs } from './update-generated-docs.mjs';

const pluginDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceDir = path.resolve(pluginDir, process.argv[2] ?? 'mermaid-source');
const referencesDir = path.join(pluginDir, 'skills/mermaid/references');
const syntaxDir = path.join(sourceDir, 'docs/syntax');
const configDir = path.join(sourceDir, 'docs/config');
const docsNavigationPath = path.join(sourceDir, 'packages/mermaid/src/docs/.vitepress/config.ts');
const configFiles = ['configuration.md', 'directives.md', 'layouts.md', 'math.md', 'theming.md', 'tidy-tree.md'];
const readmePath = path.join(pluginDir, 'README.md');

const exists = async (filePath) => {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
};

const requirePath = async (filePath, description) => {
  if (!(await exists(filePath))) {
    throw new Error(`Missing Mermaid ${description}: ${filePath}`);
  }
};

const gitCommit = (dir) => {
  try {
    return execFileSync('git', ['-C', dir, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
};

const readExistingSyncMetadata = async () => {
  if (!(await exists(readmePath))) {
    return null;
  }

  const readme = await readFile(readmePath, 'utf8');
  const match = readme.match(/Last synced from Mermaid: [^@]+ @ ([0-9a-f]+|unknown) on ([^\n]+)/);
  return match ? { commit: match[1], date: match[2].trim() } : null;
};

const preflightSyncSource = async () => {
  await requirePath(syntaxDir, 'syntax directory');
  await requirePath(configDir, 'config directory');
  await requirePath(docsNavigationPath, 'docs navigation file');

  for (const file of configFiles) {
    await requirePath(path.join(configDir, file), `config doc ${file}`);
  }
};

const copyDocs = async () => {
  await rm(referencesDir, { force: true, recursive: true });
  await mkdir(referencesDir, { recursive: true });

  const syntaxFiles = (await readdir(syntaxDir)).filter((file) => file.endsWith('.md'));
  for (const file of syntaxFiles) {
    await cp(path.join(syntaxDir, file), path.join(referencesDir, file));
  }

  for (const file of configFiles) {
    await cp(path.join(configDir, file), path.join(referencesDir, `config-${file}`), {
      force: true,
    });
  }
};

const sourceCommit = gitCommit(sourceDir);
const existingSyncMetadata = await readExistingSyncMetadata();

process.env.MERMAID_SYNC_SOURCE = 'mermaid-js/mermaid';
process.env.MERMAID_SOURCE_COMMIT = sourceCommit;
process.env.MERMAID_SYNC_DATE =
  existingSyncMetadata?.commit === sourceCommit ? existingSyncMetadata.date : new Date().toISOString();
process.env.MERMAID_DOCS_NAVIGATION = path.relative(pluginDir, docsNavigationPath);

await preflightSyncSource();
await copyDocs();
await updateGeneratedDocs();
