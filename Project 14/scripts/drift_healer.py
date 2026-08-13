import subprocess
import os
import sys
import json
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def run_terraform_cmd(cmd, cwd):
    logger.info(f"Executing: {' '.join(cmd)}")
    # shell=True is required on Windows to find the terraform executable on PATH properly
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tf_dir = os.path.abspath(os.path.join(script_dir, "..", "terraform"))
    
    if not os.path.exists(tf_dir):
        logger.error(f"Terraform directory not found at: {tf_dir}")
        sys.exit(1)
        
    logger.info("Starting GitOps Infrastructure Compliance Scan...")
    
    # 1. Run terraform plan with detailed exitcode
    # 0 = Succeeded, no differences
    # 1 = Error
    # 2 = Succeeded, differences present (drift!)
    plan_cmd = ["terraform", "plan", "-detailed-exitcode", "-no-color"]
    plan_result = run_terraform_cmd(plan_cmd, tf_dir)
    
    exit_code = plan_result.returncode
    
    if exit_code == 0:
        logger.info("✅ COMPLIANCE VERIFIED: Desired state matches actual cloud state. No drift detected.")
        sys.exit(0)
    elif exit_code == 1:
        logger.error("❌ ERROR: Failed to run drift check plan.")
        logger.error(plan_result.stderr)
        sys.exit(1)
    elif exit_code == 2:
        logger.warning("🚨 STATE DRIFT DETECTED: Manual out-of-band modifications identified in AWS console!")
        
        # Parse plan stdout to give user a quick overview of what drifted
        drift_details = []
        for line in plan_result.stdout.splitlines():
            if any(marker in line for marker in ["will be updated in-place", "will be created", "will be destroyed", "must be replaced"]):
                drift_details.append(line.strip())
                
        if drift_details:
            logger.warning("Drift Details Identified:")
            for detail in drift_details:
                logger.warning(f"  - {detail}")
        else:
            logger.warning("Check Terraform plan logs for specific parameter modifications.")
            
        # 2. Trigger Auto-Reconciliation
        logger.info("Initiating Self-Healing: Applying Git-declared configurations to overwrite manual changes...")
        apply_cmd = ["terraform", "apply", "-auto-approve", "-no-color"]
        apply_result = run_terraform_cmd(apply_cmd, tf_dir)
        
        if apply_result.returncode == 0:
            logger.info("✅ SELF-HEALING COMPLETE: Infrastructure successfully restored to Git-declared state.")
            
            # Create a simulated Slack hook payload
            slack_alert = {
                "channel": "#secops-compliance-alerts",
                "username": "GitOps-Self-Healer",
                "text": "🚨 *INFRASTRUCTURE DRIFT RECONCILED* 🚨\n"
                        f"*Target Folder:* `Project 14/terraform`\n"
                        f"*State:* Self-Healing Triggered & Completed Successfully.\n"
                        "*Resolution:* Overwrote manual cloud configuration edits to match Git master configuration."
            }
            logger.info("SIMULATED SECURE SLACK NOTIFICATION:\n%s", json.dumps(slack_alert, indent=2))
        else:
            logger.error("❌ SELF-HEALING FAILED: Manual drift overwrite could not be applied.")
            logger.error(apply_result.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
