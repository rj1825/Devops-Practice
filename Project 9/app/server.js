const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    project: 'Project 9: DevSecOps Compliance Pipeline',
    message: 'Welcome to the secure Node.js application!',
    timestamp: new Date().toISOString()
  });
});

app.get('/status', (req, res) => {
  res.json({
    app: 'running',
    securityScanLevel: 'high'
  });
});

app.listen(PORT, () => {
  console.log(`Application is running on port ${PORT}`);
});
