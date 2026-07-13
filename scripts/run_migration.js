const https = require('https');
const fs = require('fs');

const path = require('path');

// Load environment variables from root .env if it exists
try {
  const envPath = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split(/\r?\n/).forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const parts = trimmed.split('=');
        const key = parts[0].trim();
        const value = parts.slice(1).join('=').trim();
        process.env[key] = value;
      }
    });
  }
} catch (e) {}

const PAT = process.env.SUPABASE_PAT || process.env.SUPABASE_SERVICE_ROLE_KEY || 'your_personal_access_token_here';
const PROJECT_ID = process.env.SUPABASE_PROJECT_ID || 'ykigxzsgiuejnslbdkij';

const sql = fs.readFileSync('supabase/migrations/001_initial_schema.sql', 'utf8');

const payload = JSON.stringify({
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/call',
  params: {
    name: 'apply_migration',
    arguments: { 
      project_id: PROJECT_ID, 
      name: '001_initial_schema',
      query: sql 
    }
  }
});

const options = {
  hostname: 'mcp.supabase.com',
  path: '/mcp',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${PAT}`,
    'Content-Length': Buffer.byteLength(payload)
  }
};

const req = https.request(options, res => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    console.log('Status:', res.statusCode);
    console.log('Response:', data.slice(0, 1000));
  });
});
req.on('error', e => console.error('Error:', e.message));
req.write(payload);
req.end();
