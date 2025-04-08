#!/usr/bin/env python3
"""
End-to-End SEO Audit Workflow with Screaming Frog Integration

This script automates the entire SEO audit process from crawling the site
with Screaming Frog to generating reports with prioritized recommendations.

Usage:
    python full_workflow.py --domain example.com --crawl-url https://example.com
"""

import os
import argparse
import datetime
import logging
import json
from pathlib import Path
from screaming_frog_automation import ScreamingFrogAutomation
from seo_audit_automation import SEOAuditAutomation
from workflow import SEOWorkflow


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("full_seo_workflow.log"),
        logging.StreamHandler()
    ]
)

class EndToEndSEOWorkflow:
    """
    A class to manage the complete SEO audit workflow from crawling to reporting
    """
    
    def __init__(self, domain, sf_path=None):
        """
        Initialize the end-to-end SEO workflow
        
        Args:
            domain (str): The domain being audited
            sf_path (str, optional): Path to the Screaming Frog executable
        """
        self.domain = domain
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_dir = os.path.join("projects", f"{domain}_{self.timestamp}")
        self.exports_dir = os.path.join(self.base_dir, "exports")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        
        # Create required directories
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize Screaming Frog automation
        self.sf_automation = ScreamingFrogAutomation(sf_path)
        
        logging.info(f"Initialized End-to-End SEO workflow for {domain}")
        logging.info(f"Base directory: {self.base_dir}")
    
    def run_crawl(self, url, max_urls=None, config_file=None, custom_export_tabs=None):
        """Run Screaming Frog crawl with automatic exports"""
        logging.info(f"Starting Screaming Frog crawl of {url}")
        
        # Default export tabs for SEO audit
        export_tabs = custom_export_tabs or [
            'Internal:All',
            'Internal:HTML',
            'Response Codes',
            'Page Titles',
            'Meta Description',
            'H1',
            'Images',
            'Redirect Chains',
            'All Inlinks',
            'Page Speed'
        ]
        
        # Run the crawl with exports
        success = self.sf_automation.run_crawl_with_exports(
            url=url,
            output_dir=self.exports_dir,
            export_tabs=export_tabs,
            config_file=config_file
        )
        
        if not success:
            logging.error("Screaming Frog crawl failed. Workflow aborted.")
            return False
        
        logging.info(f"Screaming Frog crawl completed. Exports saved to {self.exports_dir}")
        return True
    
    def run_seo_audit(self):
        """Run SEO audit on the exported data"""
        logging.info("Starting SEO audit analysis...")
        
        # Create audit automation instance
        audit = SEOAuditAutomation(self.exports_dir)
        
        # Load files
        if not audit.load_files():
            logging.error("Failed to load export files. Audit aborted.")
            return False
        
        # Run analysis
        audit.run_analysis()
        
        # Generate reports
        json_report = audit.generate_report(self.reports_dir)
        charts_file = audit.generate_charts(self.reports_dir)
        html_report = audit.generate_html_report(self.reports_dir)
        
        self.report_files = {
            "json": json_report,
            "charts": charts_file,
            "html": html_report
        }
        
        logging.info("SEO audit completed successfully")
        
        # Return report summary
        with open(json_report, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data["summary"]
    
    def run_full_workflow(self, url, max_urls=None, config_file=None, 
                         send_email=False, email_config=None):
        """Run the complete end-to-end workflow"""
        logging.info(f"Starting complete end-to-end SEO workflow for {self.domain}")
        
        # Step 1: Run Screaming Frog crawl
        if not self.run_crawl(url, max_urls, config_file):
            return False
        
        # Step 2: Run SEO audit
        summary = self.run_seo_audit()
        if not summary:
            return False
        
        # Step 3: Generate final reports using the SEOWorkflow
        workflow = SEOWorkflow(self.domain, self.exports_dir, self.reports_dir)
        workflow.generate_excel_report()
        
        # Step 4: Send email if requested
        if send_email and email_config:
            workflow.send_email_report(
                email_config["recipients"],
                email_config["smtp_server"],
                email_config["smtp_port"],
                email_config["smtp_user"],
                email_config["smtp_password"]
            )
        
        logging.info(f"End-to-end SEO workflow completed for {self.domain}")
        logging.info(f"All reports available in {self.reports_dir}")
        return True


def main():
    """Main function to run the end-to-end SEO workflow"""
    parser = argparse.ArgumentParser(description="End-to-End SEO Audit Workflow")
    parser.add_argument("--domain", required=True, help="Domain being audited (e.g., example.com)")
    parser.add_argument("--crawl-url", required=True, help="URL to crawl (e.g., https://example.com)")
    parser.add_argument("--sf-path", help="Path to Screaming Frog executable (optional)")
    parser.add_argument("--max-urls", type=int, help="Maximum URLs to crawl")
    parser.add_argument("--config-file", help="Path to Screaming Frog config file")
    parser.add_argument("--send-email", action="store_true", help="Send email with reports")
    parser.add_argument("--email-recipients", help="Comma-separated list of email recipients")
    parser.add_argument("--smtp-server", help="SMTP server for sending email")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP port (default: 587)")
    parser.add_argument("--smtp-user", help="SMTP username")
    parser.add_argument("--smtp-password", help="SMTP password")
    
    args = parser.parse_args()
    
    # Create end-to-end workflow instance
    workflow = EndToEndSEOWorkflow(args.domain, args.sf_path)
    
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
    
    # Run the full workflow
    workflow.run_full_workflow(
        url=args.crawl_url,
        max_urls=args.max_urls,
        config_file=args.config_file,
        send_email=args.send_email,
        email_config=email_config
    )


if __name__ == "__main__":
    main()