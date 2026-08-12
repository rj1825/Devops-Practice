const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { validatePolicy } = require('./policies/guardrails');

const app = express();
const PORT = process.env.PORT || 8080;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const SERVICES_FILE = path.join(__dirname, 'services.json');
const BUILDS_DIR = path.join(__dirname, 'builds');

// Ensure database and builds directories exist
if (!fs.existsSync(SERVICES_FILE)) {
  fs.writeFileSync(SERVICES_FILE, JSON.stringify([]));
}
if (!fs.existsSync(BUILDS_DIR)) {
  fs.mkdirSync(BUILDS_DIR);
}

// Helper to read services db
function getServices() {
  return JSON.parse(fs.readFileSync(SERVICES_FILE, 'utf-8'));
}

// Helper to write services db
function saveServices(services) {
  fs.writeFileSync(SERVICES_FILE, JSON.stringify(services, null, 2));
}

// API: Get active services list
app.get('/api/services', (req, res) => {
  res.json(getServices());
});

// API: Trigger self-service provisioning (with SSE log streaming)
app.post('/api/provision', (req, res) => {
  const { serviceType, name, params } = req.body;
  
  if (!serviceType || !name || !params) {
    return res.status(400).json({ error: "Missing required fields: serviceType, name, or params." });
  }

  // 1. Run Policy Guardrails Validation
  const policyCheck = validatePolicy(serviceType, params);
  if (!policyCheck.isValid) {
    return res.status(400).json({ error: policyCheck.error });
  }

  // 2. Prepare dynamic build directory
  const buildId = `${serviceType}-${name}-${Date.now()}`;
  const buildPath = path.join(BUILDS_DIR, buildId);
  fs.mkdirSync(buildPath);

  // 3. Copy Terraform template files
  const templatePath = path.join(__dirname, 'templates', serviceType);
  fs.copyFileSync(path.join(templatePath, 'main.tf'), path.join(buildPath, 'main.tf'));

  // 4. Generate variables file (terraform.tfvars)
  let tfvarsContent = '';
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === 'string') {
      tfvarsContent += `${key} = "${value}"\n`;
    } else {
      tfvarsContent += `${key} = ${value}\n`;
    }
  }
  fs.writeFileSync(path.join(buildPath, 'terraform.tfvars'), tfvarsContent);

  // 5. Establish Server-Sent Events stream to client
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const sendLog = (message, status = 'building') => {
    res.write(`data: ${JSON.stringify({ log: message, status })}\n\n`);
  };

  sendLog(`Initializing provisioning for ${serviceType.toUpperCase()} service: "${name}"...`);
  sendLog(`Build Workspace: ${buildPath}`);
  sendLog(`Policy engine validated: PASS.`);

  // 6. Spawn Terraform Init
  const tfInit = spawn('terraform', ['init'], { cwd: buildPath, shell: true });

  tfInit.stdout.on('data', (data) => sendLog(data.toString()));
  tfInit.stderr.on('data', (data) => sendLog(`[stderr] ${data.toString()}`));

  tfInit.on('close', (code) => {
    if (code !== 0) {
      sendLog(`Terraform initialization failed with exit code ${code}`, 'failed');
      return res.end();
    }

    sendLog(`Terraform initialized successfully. Running validation plan...`);

    // 7. Spawn Terraform Plan/Apply
    // Note: Since this is local, we run Plan only to avoid creating real charges, or run Apply if the user has keys.
    // We will do a full 'terraform plan' to demonstrate IaC validation without creating billing.
    const tfPlan = spawn('terraform', ['plan', '-no-color'], { cwd: buildPath, shell: true });

    tfPlan.stdout.on('data', (data) => sendLog(data.toString()));
    tfPlan.stderr.on('data', (data) => sendLog(`[stderr] ${data.toString()}`));

    tfPlan.on('close', (planCode) => {
      if (planCode !== 0) {
        sendLog(`Terraform plan validation failed with exit code ${planCode}`, 'failed');
        return res.end();
      }

      sendLog(`Terraform plan generated successfully. Provisioning resources...`);
      sendLog(`[SYSTEM] Simulation complete. Adding resource to active service directory.`, 'success');

      // Add resource to internal database
      const services = getServices();
      services.push({
        id: buildId,
        name: name,
        type: serviceType,
        params: params,
        status: 'Active',
        created_at: new Date().toISOString()
      });
      saveServices(services);

      res.end();
    });
  });
});

// API: Delete provisioned resource record
app.delete('/api/services/:id', (req, res) => {
  const { id } = req.params;
  let services = getServices();
  const index = services.findIndex(s => s.id === id);

  if (index === -1) {
    return res.status(404).json({ error: "Service not found." });
  }

  // Remove directory and data record
  const buildPath = path.join(BUILDS_DIR, id);
  if (fs.existsSync(buildPath)) {
    fs.rmSync(buildPath, { recursive: true, force: true });
  }

  services.splice(index, 1);
  saveServices(services);
  res.json({ success: true });
});

app.listen(PORT, () => {
  console.log(`Internal Developer Platform backend running on http://localhost:${PORT}`);
});
