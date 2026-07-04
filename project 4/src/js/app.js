document.addEventListener('DOMContentLoaded', () => {
  console.log('Enterprise Static Asset Delivery Platform Loaded.');
  
  const statusEl = document.getElementById('delivery-status');
  if (statusEl) {
    statusEl.textContent = 'Delivered via AWS CloudFront CDN with WAF protection';
  }
});
