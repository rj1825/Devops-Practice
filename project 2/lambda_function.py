import os
import json
import datetime
import logging
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

# Configure Logger
logger = logging.getLogger("cost_optimizer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Approximate AWS monthly pricing defaults (us-east-1)
PRICING = {
    "eip_per_hour": 0.005,      # ~$3.60/month
    "ebs_gp3_per_gb": 0.08,    # ~$8.00/month for 100GB
    "snapshot_per_gb": 0.05,   # ~$5.00/month for 100GB
    "alb_per_hour": 0.0225,    # ~$16.20/month
}

def load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config.json: {e}")
        # Default fallback config
        return {
            "dry_run": True,
            "regions": ["us-east-1"],
            "cleanup_settings": {
                "unused_eip": True,
                "orphaned_ebs": true,
                "old_snapshots": true,
                "idle_load_balancers": false
            },
            "rules": {
                "ebs_orphan_days": 7,
                "snapshot_max_age_days": 30,
                "idle_alb_request_threshold": 100
            },
            "notifications": {
                "sns_topic_arn": "",
                "s3_report_bucket": ""
            }
        }

def scan_region_costs(region: str, config: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Scanning region: {region}")
    session = boto3.Session(region_name=region)
    ec2_client = session.client('ec2')
    elbv2_client = session.client('elbv2')
    
    results = {
        "region": region,
        "eip": [],
        "ebs": [],
        "snapshots": [],
        "elbv2": [],
        "savings_estimated": 0.0
    }
    
    # 1. Check Unassociated Elastic IPs
    if config["cleanup_settings"]["unused_eip"]:
        try:
            addresses = ec2_client.describe_addresses()["Addresses"]
            for addr in addresses:
                if "AssociationId" not in addr:
                    public_ip = addr.get("PublicIp", "Unknown")
                    allocation_id = addr.get("AllocationId", "")
                    monthly_cost = PRICING["eip_per_hour"] * 24 * 30
                    
                    eip_info = {
                        "id": allocation_id,
                        "ip": public_ip,
                        "monthly_cost": monthly_cost
                    }
                    
                    if not config["dry_run"]:
                        try:
                            ec2_client.release_address(AllocationId=allocation_id)
                            eip_info["status"] = "Released"
                        except Exception as e:
                            eip_info["status"] = f"Failed to release: {str(e)}"
                    else:
                        eip_info["status"] = "Dry-Run: Flagged"
                    
                    results["eip"].append(eip_info)
                    results["savings_estimated"] += monthly_cost
        except ClientError as e:
            logger.error(f"Error checking EIPs in {region}: {e}")

    # 2. Check Orphaned EBS Volumes
    if config["cleanup_settings"]["orphaned_ebs"]:
        try:
            volumes = ec2_client.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )["Volumes"]
            
            now = datetime.datetime.now(datetime.timezone.utc)
            max_age_days = config["rules"]["ebs_orphan_days"]
            
            for vol in volumes:
                create_time = vol["CreateTime"]
                age_days = (now - create_time).days
                
                if age_days >= max_age_days:
                    vol_id = vol["VolumeId"]
                    size = vol["Size"]
                    vol_type = vol["VolumeType"]
                    monthly_cost = size * PRICING["ebs_gp3_per_gb"]
                    
                    vol_info = {
                        "id": vol_id,
                        "size_gb": size,
                        "age_days": age_days,
                        "monthly_cost": monthly_cost
                    }
                    
                    if not config["dry_run"]:
                        try:
                            ec2_client.delete_volume(VolumeId=vol_id)
                            vol_info["status"] = "Deleted"
                        except Exception as e:
                            vol_info["status"] = f"Failed to delete: {str(e)}"
                    else:
                        vol_info["status"] = "Dry-Run: Flagged"
                        
                    results["ebs"].append(vol_info)
                    results["savings_estimated"] += monthly_cost
        except ClientError as e:
            logger.error(f"Error checking EBS volumes in {region}: {e}")

    # 3. Check Outdated Snapshots
    if config["cleanup_settings"]["old_snapshots"]:
        try:
            snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])["Snapshots"]
            now = datetime.datetime.now(datetime.timezone.utc)
            max_age_days = config["rules"]["snapshot_max_age_days"]
            
            for snap in snapshots:
                start_time = snap["StartTime"]
                age_days = (now - start_time).days
                
                if age_days >= max_age_days:
                    snap_id = snap["SnapshotId"]
                    vol_size = snap.get("VolumeSize", 0)
                    monthly_cost = vol_size * PRICING["snapshot_per_gb"]
                    
                    snap_info = {
                        "id": snap_id,
                        "volume_size": vol_size,
                        "age_days": age_days,
                        "monthly_cost": monthly_cost
                    }
                    
                    if not config["dry_run"]:
                        try:
                            ec2_client.delete_snapshot(SnapshotId=snap_id)
                            snap_info["status"] = "Deleted"
                        except Exception as e:
                            # Might fail if active AMI uses snapshot
                            snap_info["status"] = f"Failed to delete: {str(e)}"
                    else:
                        snap_info["status"] = "Dry-Run: Flagged"
                        
                    results["snapshots"].append(snap_info)
                    results["savings_estimated"] += monthly_cost
        except ClientError as e:
            logger.error(f"Error checking Snapshots in {region}: {e}")

    # 4. Check Idle Load Balancers
    if config["cleanup_settings"]["idle_load_balancers"]:
        try:
            load_balancers = elbv2_client.describe_load_balancers()["LoadBalancers"]
            for lb in load_balancers:
                lb_arn = lb["LoadBalancerArn"]
                lb_name = lb["LoadBalancerName"]
                
                # Check for target groups
                tgs = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)["TargetGroups"]
                is_idle = False
                reason = ""
                
                if not tgs:
                    is_idle = True
                    reason = "No target groups configured"
                else:
                    # Check if any target group has active targets
                    all_empty = True
                    for tg in tgs:
                        tg_arn = tg["TargetGroupArn"]
                        targets = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)["TargetHealthDescriptions"]
                        if targets:
                            all_empty = False
                            break
                    if all_empty:
                        is_idle = True
                        reason = "All target groups are empty (no registered targets)"
                
                if is_idle:
                    monthly_cost = PRICING["alb_per_hour"] * 24 * 30
                    lb_info = {
                        "id": lb_name,
                        "arn": lb_arn,
                        "reason": reason,
                        "monthly_cost": monthly_cost
                    }
                    
                    if not config["dry_run"]:
                        try:
                            elbv2_client.delete_load_balancer(LoadBalancerArn=lb_arn)
                            lb_info["status"] = "Deleted"
                        except Exception as e:
                            lb_info["status"] = f"Failed to delete: {str(e)}"
                    else:
                        lb_info["status"] = "Dry-Run: Flagged"
                        
                    results["elbv2"].append(lb_info)
                    results["savings_estimated"] += monthly_cost
        except ClientError as e:
            logger.error(f"Error checking ALBs in {region}: {e}")
            
    return results

def generate_html_report(all_results: List[Dict[str, Any]], dry_run: bool) -> str:
    total_savings = sum(r["savings_estimated"] for r in all_results)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AWS Cost Optimization Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #111827; padding: 2rem; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h1 {{ color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }}
            .metric-card {{ background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; margin: 1rem 0 2rem; }}
            .metric-card h2 {{ margin: 0; color: #1d4ed8; }}
            .metric-card p {{ margin: 5px 0 0; font-size: 1.1rem; font-weight: bold; }}
            h3 {{ color: #111827; margin-top: 2rem; background: #f9fafb; padding: 0.5rem; border-radius: 4px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 0.75rem; text-align: left; }}
            th {{ background-color: #f9fafb; font-weight: 600; }}
            .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }}
            .badge-warn {{ background-color: #fef3c7; color: #d97706; }}
            .badge-success {{ background-color: #d1fae5; color: #065f46; }}
            .badge-fail {{ background-color: #fee2e2; color: #991b1b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AWS Cloud Cost Sweep Report</h1>
            <p><strong>Date Run:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Execution Mode:</strong> <span class="badge badge-warn">{'DRY-RUN (Auditing Only)' if dry_run else 'AUTO-CLEANUP ACTIVE'}</span></p>
            
            <div class="metric-card">
                <h2>Estimated Monthly Savings</h2>
                <p>${total_savings:.2f} / month</p>
            </div>
    """
    
    for r in all_results:
        # Check if there are any waste items in this region
        has_waste = len(r["eip"]) > 0 or len(r["ebs"]) > 0 or len(r["snapshots"]) > 0 or len(r["elbv2"]) > 0
        if not has_waste:
            continue
            
        html += f"<h2>Region: {r['region']} (Potential Savings: ${r['savings_estimated']:.2f}/mo)</h2>"
        
        # EIP Table
        if r["eip"]:
            html += "<h3>Unassociated Elastic IPs</h3>"
            html += "<table><thead><tr><th>IP Address</th><th>Allocation ID</th><th>Status</th><th>Savings/Mo</th></tr></thead><tbody>"
            for item in r["eip"]:
                badge_class = "badge-warn" if "Dry-Run" in item["status"] else ("badge-success" if item["status"] == "Released" else "badge-fail")
                html += f"<tr><td>{item['ip']}</td><td>{item['id']}</td><td><span class='badge {badge_class}'>{item['status']}</span></td><td>${item['monthly_cost']:.2f}</td></tr>"
            html += "</tbody></table>"

        # EBS Table
        if r["ebs"]:
            html += "<h3>Orphaned EBS Volumes</h3>"
            html += "<table><thead><tr><th>Volume ID</th><th>Size (GB)</th><th>Age (Days)</th><th>Status</th><th>Savings/Mo</th></tr></thead><tbody>"
            for item in r["ebs"]:
                badge_class = "badge-warn" if "Dry-Run" in item["status"] else ("badge-success" if item["status"] == "Deleted" else "badge-fail")
                html += f"<tr><td>{item['id']}</td><td>{item['size_gb']}</td><td>{item['age_days']}</td><td><span class='badge {badge_class}'>{item['status']}</span></td><td>${item['monthly_cost']:.2f}</td></tr>"
            html += "</tbody></table>"

        # Snapshots Table
        if r["snapshots"]:
            html += "<h3>Outdated Snapshots</h3>"
            html += "<table><thead><tr><th>Snapshot ID</th><th>Size (GB)</th><th>Age (Days)</th><th>Status</th><th>Savings/Mo</th></tr></thead><tbody>"
            for item in r["snapshots"]:
                badge_class = "badge-warn" if "Dry-Run" in item["status"] else ("badge-success" if item["status"] == "Deleted" else "badge-fail")
                html += f"<tr><td>{item['id']}</td><td>{item['volume_size']}</td><td>{item['age_days']}</td><td><span class='badge {badge_class}'>{item['status']}</span></td><td>${item['monthly_cost']:.2f}</td></tr>"
            html += "</tbody></table>"

        # ELB Table
        if r["elbv2"]:
            html += "<h3>Idle Load Balancers</h3>"
            html += "<table><thead><tr><th>Name</th><th>Reason</th><th>Status</th><th>Savings/Mo</th></tr></thead><tbody>"
            for item in r["elbv2"]:
                badge_class = "badge-warn" if "Dry-Run" in item["status"] else ("badge-success" if item["status"] == "Deleted" else "badge-fail")
                html += f"<tr><td>{item['id']}</td><td>{item['reason']}</td><td><span class='badge {badge_class}'>{item['status']}</span></td><td>${item['monthly_cost']:.2f}</td></tr>"
            html += "</tbody></table>"
            
    html += """
        </div>
    </body>
    </html>
    """
    return html

def send_notifications(html_report: str, total_savings: float, config: Dict[str, Any]):
    sns_arn = config["notifications"].get("sns_topic_arn")
    s3_bucket = config["notifications"].get("s3_report_bucket")
    
    # 1. Save Report to S3
    if s3_bucket:
        try:
            s3_client = boto3.client('s3')
            file_name = f"cost-reports/report-{datetime.date.today().isoformat()}.html"
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=file_name,
                Body=html_report,
                ContentType='text/html'
            )
            logger.info(f"Report uploaded successfully to S3: s3://{s3_bucket}/{file_name}")
        except Exception as e:
            logger.error(f"Failed to upload report to S3: {e}")
            
    # 2. Publish summary to SNS Topic
    if sns_arn:
        try:
            sns_client = boto3.client('sns')
            subject = f"AWS Cost Optimization Alert: Save ${total_savings:.2f}/mo!"
            message = (
                f"AWS Cost Optimization Sweep Complete.\n\n"
                f"Estimated Monthly Savings: ${total_savings:.2f}\n"
                f"Dry Run Mode: {config['dry_run']}\n\n"
                f"Please check the S3 bucket: s3://{s3_bucket}/ for the full HTML reports."
            )
            sns_client.publish(
                TopicArn=sns_arn,
                Subject=subject,
                Message=message
            )
            logger.info("SNS summary published successfully.")
        except Exception as e:
            logger.error(f"Failed to publish to SNS: {e}")

def lambda_handler(event: Any, context: Any) -> Dict[str, Any]:
    config = load_config()
    all_results = []
    
    logger.info("Starting Cost Optimization Sweep...")
    
    for region in config.get("regions", ["us-east-1"]):
        region_result = scan_region_costs(region, config)
        all_results.append(region_result)
        
    total_savings = sum(r["savings_estimated"] for r in all_results)
    
    html_report = generate_html_report(all_results, config["dry_run"])
    send_notifications(html_report, total_savings, config)
    
    return {
        "statusCode": 200,
        "body": {
            "message": "Optimization sweep complete.",
            "total_savings_estimated": total_savings,
            "dry_run": config["dry_run"]
        }
    }

if __name__ == "__main__":
    # Local CLI dry-run execution
    print("Executing cost optimization locally in Dry-Run mode...")
    local_event = {}
    local_context = None
    res = lambda_handler(local_event, local_context)
    print(json.dumps(res, indent=2))
