/**
 * Policy-as-Code Guardrails Engine for the Internal Developer Platform (IDP)
 * This validates developer provisioning parameters before invoking Terraform execution.
 */

const ALLOWED_EC2_TYPES = ['t2.micro', 't2.small', 't3.micro', 't3.small'];

/**
 * Validates request arguments against corporate safety and cost policies.
 * @param {string} serviceType - 's3' or 'ec2'
 * @param {Object} params - Key-value pair configuration parameters
 * @returns {Object} { isValid: boolean, error: string|null }
 */
function validatePolicy(serviceType, params) {
  if (serviceType === 's3') {
    // 1. Enforce Server-Side Encryption
    if (params.encrypted !== true && params.encrypted !== 'true') {
      return {
        isValid: false,
        error: "POLICY VIOLATION [Security]: S3 Buckets must have Server-Side Encryption (KMS/AES256) enabled. Unencrypted buckets are prohibited."
      };
    }
    
    // 2. Validate S3 naming convention rules
    const bucketName = params.bucket_name || '';
    const nameRegex = /^[a-z0-9][a-z0-9.-]*[a-z0-9]$/;
    if (!nameRegex.test(bucketName)) {
      return {
        isValid: false,
        error: "POLICY VIOLATION [Naming]: S3 bucket name must consist of lowercase letters, numbers, dots (.), and hyphens (-)."
      };
    }
  } 
  
  else if (serviceType === 'ec2') {
    // 1. Enforce EC2 Instance Type Cost Controls
    const instanceType = params.instance_type;
    if (!ALLOWED_EC2_TYPES.includes(instanceType)) {
      return {
        isValid: false,
        error: `POLICY VIOLATION [Cost Limit]: Instance type '${instanceType}' is unauthorized. To prevent unexpected cloud spend, self-service is limited to: [${ALLOWED_EC2_TYPES.join(', ')}].`
      };
    }

    // 2. Validate Instance Name length/format
    const instanceName = params.instance_name || '';
    if (instanceName.trim().length < 3) {
      return {
        isValid: false,
        error: "POLICY VIOLATION [Naming]: Instance Name must be at least 3 characters long."
      };
    }
  }

  return { isValid: true, error: null };
}

module.exports = { validatePolicy };
