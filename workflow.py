#!/usr/bin/env python3
"""
Automated SEO Audit Workflow Script

This script automates the workflow for running SEO audits using Screaming Frog exports.
It sets up the directory structure, processes exports, and generates reports.

Usage:
    python workflow.py --domain example.com --exports_path /path/to/exports
"""

import os
import argparse
import shutil
import subprocess
import datetime
import json
import pandas as pd
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from seo_audit_automation import SEOAuditAutomation


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("seo_workflow.log"),
        logging.StreamHandler()
    ]
)

class SEOWorkflow:
    """
    A class to manage the SEO audit workflow from Screaming Frog exports to reports
    """
    
    def __init__(self, domain, exports_path, output_path=None):
        """
        Initialize the SEO workflow
        
        Args:
            domain (str): The domain being audited
            exports_path (str): Path to Screaming Frog exports
            output_path (str, optional): Path for output reports
        """
        self.domain = domain
        self.exports_path = exports_path
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = output_path or os.path.join("outputs", f"{domain}_{self.timestamp}")
        self.reports_path = os.path.join(self.output_path, "reports")
        self.report_files = {}
        
        # Create required directories
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)
        
        logging.info(f"Initialized SEO workflow for {domain}")
        logging.info(f"Exports path: {exports_path}")
        logging.info(f"Output path: {self.output_path}")
    
    def copy_exports(self):
        """Copy Screaming Frog exports to the working directory"""
        exports_dest = os.path.join(self.output_path, "exports")
        os.makedirs(exports_dest, exist_ok=True)
        
        # Copy all CSV files
        count = 0
        for filename in os.listdir(self.exports_path):
            if filename.endswith(".csv"):
                src = os.path.join(self.exports_path, filename)
                dst = os.path.join(exports_dest, filename)
                shutil.copy2(src, dst)
                count += 1
        
        logging.info(f"Copied {count} export files to {exports_dest}")
        return exports_dest
    
    def run_audit(self, exports_dir):
        """Run the SEO audit on the exported files"""
        logging.info("Starting SEO audit...")
        
        audit = SEOAuditAutomation(exports_dir)
        
        # Load files
        if not audit.load_files():
            logging.error("Failed to load export files")
            return False
        
        # Run analysis
        audit.run_analysis()
        
        # Generate reports
        json_report = audit.generate_report(self.reports_path)
        charts_file = audit.generate_charts(self.reports_path)
        html_report = audit.generate_html_report(self.reports_path)
        
        self.report_files = {
            "json": json_report,
            "charts": charts_file,
            "html": html_report
        }
        
        logging.info("SEO audit completed successfully")
        logging.info(f"JSON report: {json_report}")
        logging.info(f"Charts: {charts_file}")
        logging.info(f"HTML report: {html_report}")
        
        # Load and return the summary
        with open(json_report, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data["summary"]
    
    def generate_excel_report(self):
        """Generate Excel report with all issues"""
        logging.info("Generating Excel report...")
        
        # Load JSON data
        with open(self.report_files["json"], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create Excel writer
        excel_path = os.path.join(self.reports_path, f"seo_audit_{self.domain}_{self.timestamp}.xlsx")
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        
        # Create summary sheet
        summary_data = {
            "Metric": [
                "Domain",
                "Audit Date",
                "Total Issues",
                "Critical Issues",
                "High Priority Issues",
                "Medium Priority Issues",
                "Low Priority Issues"
            ],
            "Value": [
                self.domain,
                data["summary"]["date"],
                data["summary"]["total_issues"],
                data["summary"]["critical_count"],
                data["summary"]["high_count"],
                data["summary"]["medium_count"],
                data["summary"]["low_count"]
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        # Format summary sheet
        workbook = writer.book
        summary_sheet = writer.sheets["Summary"]
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(summary_df.columns.values):
            summary_sheet.write(0, col_num, value, header_format)
        
        # Add issue sheets for each category
        categories = ["critical", "high", "medium", "low"]
        
        for category in categories:
            if data["issues"][category]:
                # Prepare data for this category
                issue_data = []
                for issue in data["issues"][category]:
                    for example in issue["examples"]:
                        issue_data.append({
                            "Issue Type": issue["title"],
                            "URL": example,
                            "Impact (1-10)": issue["impact"],
                            "Effort (1-10)": issue["effort"],
                            "Priority Score": issue["priority_score"],
                            "Recommendation": issue["recommendation"]
                        })
                
                # Create DataFrame and write to Excel
                if issue_data:
                    issue_df = pd.DataFrame(issue_data)
                    sheet_name = category.capitalize()
                    issue_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Format sheet
                    sheet = writer.sheets[sheet_name]
                    for col_num, value in enumerate(issue_df.columns.values):
                        sheet.write(0, col_num, value, header_format)
        
        # Save Excel file
        writer.close()
        
        logging.info(f"Excel report generated: {excel_path}")
        self.report_files["excel"] = excel_path
        return excel_path
    
    def send_email_report(self, recipients, smtp_server, smtp_port, smtp_user, smtp_password):
        """Send email with reports attached"""
        logging.info(f"Sending email report to {recipients}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"SEO Audit Report for {self.domain} - {self.timestamp}"
        
        # Load summary data
        with open(self.report_files["json"], 'r', encoding='utf-8') as f:
            data = json.load(f)
            summary = data["summary"]
        
        # Email body
        body = f"""
        <html>
        <body>
            <h1>SEO Audit Report for {self.domain}</h1>
            <p>Date: {summary['date']}</p>
            
            <h2>Summary of Findings</h2>
            <ul>
                <li><strong>Total Issues:</strong> {summary['total_issues']}</li>
                <li><strong>Critical Issues:</strong> {summary['critical_count']}</li>
                <li><strong>High Priority Issues:</strong> {summary['high_count']}</li>
                <li><strong>Medium Priority Issues:</strong> {summary['medium_count']}</li>
                <li><strong>Low Priority Issues:</strong> {summary['low_count']}</li>
            </ul>
            
            <p>Please see the attached reports for details.</p>
            
            <p>This report was automatically generated.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach files
        for report_type, file_path in self.report_files.items():
            if os.path.exists(file_path):
                attachment = open(file_path, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                
                filename = os.path.basename(file_path)
                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                msg.attach(part)
                attachment.close()
        
        # Send email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            logging.info("Email sent successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False
    
    def run_workflow(self, send_email=False, email_config=None):
        """Run the complete workflow"""
        logging.info(f"Starting complete SEO audit workflow for {self.domain}")
        
        # Step 1: Copy exports
        exports_dir = self.copy_exports()
        
        # Step 2: Run audit
        summary = self.run_audit(exports_dir)
        if not summary:
            logging.error("Audit failed. Workflow aborted.")
            return False
        
        # Step 3: Generate Excel report
        self.generate_excel_report()
        
        # Step 4: Send email if requested
        if send_email and email_config:
            self.send_email_report(
                email_config["recipients"],
                email_config["smtp_server"],
                email_config["smtp_port"],
                email_config["smtp_user"],
                email_config["smtp_password"]
            )
        
        logging.info(f"SEO audit workflow completed for {self.domain}")
        return self.report_files


def main():
    """Main function to run the SEO workflow"""
    parser = argparse.ArgumentParser(description="Automate SEO audit workflow")
    parser.add_argument("--domain", required=True, help="Domain being audited")
    parser.add_argument("--exports_path", required=True, help="Directory containing Screaming Frog export files")
    parser.add_argument("--output_path", help="Output directory for reports (optional)")
    parser.add_argument("--send_email", action="store_true", help="Send email with reports")
    parser.add_argument("--email_recipients", help="Comma-separated list of email recipients")
    parser.add_argument("--smtp_server", help="SMTP server for sending email")
    parser.add_argument("--smtp_port", type=int, default=587, help="SMTP port (default: 587)")
    parser.add_argument("--smtp_user", help="SMTP username")
    parser.add_argument("--smtp_password", help="SMTP password")
    
    args = parser.parse_args()
    
    # Create workflow instance
    workflow = SEOWorkflow(args.domain, args.exports_path, args.output_path)
    
    # Email configuration
    email_config = None
    if args.send_email:
        if not all([args.email_recipients, args.smtp_server, args.smtp_user, args.smtp_password]):
            logging.error("Email sending requires recipients, SMTP server, user and password")
            return
        
        email_config = {
            "recipients": args.email_recipients.split(","),
            "smtp_server": args.smtp_server,
            "smtp_port": args.smtp_port,
            "smtp_user": args.smtp_user,
            "smtp_password": args.smtp_password
        }
    
    # Run the workflow
    workflow.run_workflow(args.send_email, email_config)


if __name__ == "__main__":
    main()