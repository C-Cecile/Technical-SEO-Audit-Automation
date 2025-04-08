import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import matplotlib.pyplot as plt
from pathlib import Path

class SEOAuditAutomation:
    """
    A class to automate SEO audit processing from Screaming Frog exports
    """
    
    # Define impact and effort scores for different issues
    ISSUE_SCORES = {
        # Critical issues
        "broken_links": {"impact": 10, "effort": 5, "category": "critical"},
        "server_errors": {"impact": 10, "effort": 6, "category": "critical"},
        "redirect_chains": {"impact": 9, "effort": 4, "category": "critical"},
        "duplicate_titles": {"impact": 8, "effort": 3, "category": "critical"},
        
        # High priority issues
        "missing_meta_descriptions": {"impact": 7, "effort": 2, "category": "high"},
        "missing_h1": {"impact": 7, "effort": 2, "category": "high"},
        "duplicate_content": {"impact": 8, "effort": 6, "category": "high"},
        "slow_pages": {"impact": 7, "effort": 7, "category": "high"},
        
        # Medium priority issues
        "title_too_long": {"impact": 5, "effort": 2, "category": "medium"},
        "description_too_long": {"impact": 5, "effort": 2, "category": "medium"},
        "low_word_count": {"impact": 6, "effort": 5, "category": "medium"},
        "missing_alt_text": {"impact": 5, "effort": 4, "category": "medium"},
        
        # Low priority issues
        "multiple_h1": {"impact": 3, "effort": 2, "category": "low"},
        "missing_meta_keywords": {"impact": 2, "effort": 1, "category": "low"},
        "excessive_outlinks": {"impact": 3, "effort": 4, "category": "low"},
        "low_text_html_ratio": {"impact": 3, "effort": 5, "category": "low"}
    }
    
    def __init__(self, export_dir):
        """
        Initialize the SEO audit automation
        
        Args:
            export_dir (str): Path to the directory containing Screaming Frog exports
        """
        self.export_dir = export_dir
        self.files = {}
        self.data = {}
        self.issues = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        self.summary = {}
        
    def load_files(self):
        """Load all CSV files from the export directory"""
        try:
            # Expected file names from Screaming Frog
            expected_files = [
                "internal_all.csv",
                "internal_html.csv",
                "response_codes.csv",
                "page_titles.csv",
                "meta_description.csv",
                "h1.csv",
                "images.csv",
                "redirect_chains.csv",
                "all_inlinks.csv",
                "page_speed.csv"
            ]
            
            for filename in os.listdir(self.export_dir):
                if filename.endswith(".csv"):
                    file_path = os.path.join(self.export_dir, filename)
                    for expected in expected_files:
                        if expected.lower() in filename.lower():
                            self.files[expected.replace(".csv", "")] = file_path
                            break
            
            # Load each file into pandas DataFrame
            for key, file_path in self.files.items():
                print(f"Loading {key} from {file_path}")
                try:
                    self.data[key] = pd.read_csv(file_path, encoding='utf-8')
                except:
                    # Try with different encoding if UTF-8 fails
                    try:
                        self.data[key] = pd.read_csv(file_path, encoding='latin1')
                    except Exception as e:
                        print(f"Error loading {file_path}: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error loading files: {e}")
            return False
    
    def analyze_broken_links(self):
        """Identify broken links (4xx and 5xx responses)"""
        if "response_codes" not in self.data:
            return
        
        df = self.data["response_codes"]
        
        # Find 4xx client errors
        client_errors = df[df["Status Code"].between(400, 499)]
        if not client_errors.empty:
            issue = {
                "type": "broken_links",
                "title": "Broken Links (4xx)",
                "description": "Pages returning client error status codes",
                "count": len(client_errors),
                "examples": client_errors["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["broken_links"]["impact"],
                "effort": self.ISSUE_SCORES["broken_links"]["effort"],
                "priority_score": self.ISSUE_SCORES["broken_links"]["impact"] / self.ISSUE_SCORES["broken_links"]["effort"],
                "recommendation": "Fix or redirect broken links to maintain user experience and link equity"
            }
            self.issues["critical"].append(issue)
        
        # Find 5xx server errors
        server_errors = df[df["Status Code"].between(500, 599)]
        if not server_errors.empty:
            issue = {
                "type": "server_errors",
                "title": "Server Errors (5xx)",
                "description": "Pages returning server error status codes",
                "count": len(server_errors),
                "examples": server_errors["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["server_errors"]["impact"],
                "effort": self.ISSUE_SCORES["server_errors"]["effort"],
                "priority_score": self.ISSUE_SCORES["server_errors"]["impact"] / self.ISSUE_SCORES["server_errors"]["effort"],
                "recommendation": "Investigate server issues and fix the root cause to ensure page availability"
            }
            self.issues["critical"].append(issue)
    
    def analyze_redirect_chains(self):
        """Identify redirect chains"""
        if "redirect_chains" not in self.data:
            return
        
        df = self.data["redirect_chains"]
        
        # Find chains with more than 1 redirect
        if "Redirect Chain" in df.columns:
            chains = df[df["Redirect Chain"] > 1]
            if not chains.empty:
                issue = {
                    "type": "redirect_chains",
                    "title": "Redirect Chains",
                    "description": "URLs with multiple redirects in sequence",
                    "count": len(chains),
                    "examples": chains["Address"].head(5).tolist(),
                    "impact": self.ISSUE_SCORES["redirect_chains"]["impact"],
                    "effort": self.ISSUE_SCORES["redirect_chains"]["effort"],
                    "priority_score": self.ISSUE_SCORES["redirect_chains"]["impact"] / self.ISSUE_SCORES["redirect_chains"]["effort"],
                    "recommendation": "Reduce redirect chains to a single redirect to improve page speed and reduce crawl budget waste"
                }
                self.issues["critical"].append(issue)
    
    def analyze_duplicate_titles(self):
        """Identify duplicate page titles"""
        if "page_titles" not in self.data:
            return
            
        df = self.data["page_titles"]
        
        # Skip rows without title
        df = df.dropna(subset=["Title 1"])
        
        # Count occurrences of each title
        title_counts = df["Title 1"].value_counts()
        
        # Find titles that occur more than once
        duplicate_titles = title_counts[title_counts > 1].index.tolist()
        
        if duplicate_titles:
            # Get examples of URLs with duplicate titles
            examples = []
            for title in duplicate_titles[:5]:
                urls = df[df["Title 1"] == title]["Address"].head(2).tolist()
                examples.extend(urls)
            
            issue = {
                "type": "duplicate_titles",
                "title": "Duplicate Page Titles",
                "description": "Multiple pages using the same title",
                "count": len(duplicate_titles),
                "examples": examples[:5],
                "impact": self.ISSUE_SCORES["duplicate_titles"]["impact"],
                "effort": self.ISSUE_SCORES["duplicate_titles"]["effort"],
                "priority_score": self.ISSUE_SCORES["duplicate_titles"]["impact"] / self.ISSUE_SCORES["duplicate_titles"]["effort"],
                "recommendation": "Create unique page titles to improve SEO and user experience"
            }
            self.issues["critical"].append(issue)
    
    def analyze_missing_meta_descriptions(self):
        """Identify pages with missing meta descriptions"""
        if "meta_description" not in self.data:
            return
            
        df = self.data["meta_description"]
        
        # Find rows with missing meta description
        missing = df[df["Meta Description 1"].isna()]
        
        if not missing.empty:
            issue = {
                "type": "missing_meta_descriptions",
                "title": "Missing Meta Descriptions",
                "description": "Pages without meta descriptions",
                "count": len(missing),
                "examples": missing["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["missing_meta_descriptions"]["impact"],
                "effort": self.ISSUE_SCORES["missing_meta_descriptions"]["effort"],
                "priority_score": self.ISSUE_SCORES["missing_meta_descriptions"]["impact"] / self.ISSUE_SCORES["missing_meta_descriptions"]["effort"],
                "recommendation": "Add compelling meta descriptions to improve click-through rates from search results"
            }
            self.issues["high"].append(issue)
    
    def analyze_missing_h1(self):
        """Identify pages with missing H1 tags"""
        if "h1" not in self.data:
            return
            
        df = self.data["h1"]
        
        # Find rows with missing H1
        missing = df[df["H1-1"].isna()]
        
        if not missing.empty:
            issue = {
                "type": "missing_h1",
                "title": "Missing H1 Tags",
                "description": "Pages without H1 headings",
                "count": len(missing),
                "examples": missing["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["missing_h1"]["impact"],
                "effort": self.ISSUE_SCORES["missing_h1"]["effort"],
                "priority_score": self.ISSUE_SCORES["missing_h1"]["impact"] / self.ISSUE_SCORES["missing_h1"]["effort"],
                "recommendation": "Add H1 tags to all pages to improve content hierarchy and relevance signals"
            }
            self.issues["high"].append(issue)
    
    def analyze_slow_pages(self):
        """Identify slow-loading pages"""
        if "page_speed" not in self.data:
            return
            
        df = self.data["page_speed"]
        
        # Define threshold for slow pages (in seconds)
        threshold = 3.0
        
        # Find rows with load time above threshold
        if "Page Load Time (Seconds)" in df.columns:
            slow_pages = df[df["Page Load Time (Seconds)"] > threshold]
            
            if not slow_pages.empty:
                issue = {
                    "type": "slow_pages",
                    "title": "Slow-Loading Pages",
                    "description": f"Pages with load time greater than {threshold} seconds",
                    "count": len(slow_pages),
                    "examples": slow_pages["Address"].head(5).tolist(),
                    "impact": self.ISSUE_SCORES["slow_pages"]["impact"],
                    "effort": self.ISSUE_SCORES["slow_pages"]["effort"],
                    "priority_score": self.ISSUE_SCORES["slow_pages"]["impact"] / self.ISSUE_SCORES["slow_pages"]["effort"],
                    "recommendation": "Optimize page speed by reducing file sizes, implementing caching, and minimizing render-blocking resources"
                }
                self.issues["high"].append(issue)
    
    def analyze_title_length(self):
        """Identify page titles that are too long"""
        if "page_titles" not in self.data:
            return
            
        df = self.data["page_titles"]
        
        # Skip rows without title
        df = df.dropna(subset=["Title 1"])
        
        # Define max length for titles (characters)
        max_length = 60
        
        # Find titles that are too long
        long_titles = df[df["Title 1"].str.len() > max_length]
        
        if not long_titles.empty:
            issue = {
                "type": "title_too_long",
                "title": "Page Titles Too Long",
                "description": f"Page titles longer than {max_length} characters",
                "count": len(long_titles),
                "examples": long_titles["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["title_too_long"]["impact"],
                "effort": self.ISSUE_SCORES["title_too_long"]["effort"],
                "priority_score": self.ISSUE_SCORES["title_too_long"]["impact"] / self.ISSUE_SCORES["title_too_long"]["effort"],
                "recommendation": f"Shorten page titles to under {max_length} characters to avoid truncation in search results"
            }
            self.issues["medium"].append(issue)
    
    def analyze_description_length(self):
        """Identify meta descriptions that are too long"""
        if "meta_description" not in self.data:
            return
            
        df = self.data["meta_description"]
        
        # Skip rows without description
        df = df.dropna(subset=["Meta Description 1"])
        
        # Define max length for descriptions (characters)
        max_length = 160
        
        # Find descriptions that are too long
        long_descriptions = df[df["Meta Description 1"].str.len() > max_length]
        
        if not long_descriptions.empty:
            issue = {
                "type": "description_too_long",
                "title": "Meta Descriptions Too Long",
                "description": f"Meta descriptions longer than {max_length} characters",
                "count": len(long_descriptions),
                "examples": long_descriptions["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["description_too_long"]["impact"],
                "effort": self.ISSUE_SCORES["description_too_long"]["effort"],
                "priority_score": self.ISSUE_SCORES["description_too_long"]["impact"] / self.ISSUE_SCORES["description_too_long"]["effort"],
                "recommendation": f"Shorten meta descriptions to under {max_length} characters to avoid truncation in search results"
            }
            self.issues["medium"].append(issue)
    
    def analyze_missing_alt_text(self):
        """Identify images missing alt text"""
        if "images" not in self.data:
            return
            
        df = self.data["images"]
        
        # Find images missing alt text
        missing_alt = df[df["Alt Text"].isna()]
        
        if not missing_alt.empty:
            issue = {
                "type": "missing_alt_text",
                "title": "Images Missing Alt Text",
                "description": "Images without alternative text",
                "count": len(missing_alt),
                "examples": missing_alt["Address"].head(5).tolist(),
                "impact": self.ISSUE_SCORES["missing_alt_text"]["impact"],
                "effort": self.ISSUE_SCORES["missing_alt_text"]["effort"],
                "priority_score": self.ISSUE_SCORES["missing_alt_text"]["impact"] / self.ISSUE_SCORES["missing_alt_text"]["effort"],
                "recommendation": "Add descriptive alt text to all images to improve accessibility and image search visibility"
            }
            self.issues["medium"].append(issue)
    
    def analyze_multiple_h1(self):
        """Identify pages with multiple H1 tags"""
        if "h1" not in self.data:
            return
            
        df = self.data["h1"]
        
        # Check if H1-2 column exists (indicating multiple H1 tags)
        if "H1-2" in df.columns:
            multiple_h1 = df.dropna(subset=["H1-2"])
            
            if not multiple_h1.empty:
                issue = {
                    "type": "multiple_h1",
                    "title": "Multiple H1 Tags",
                    "description": "Pages with more than one H1 heading",
                    "count": len(multiple_h1),
                    "examples": multiple_h1["Address"].head(5).tolist(),
                    "impact": self.ISSUE_SCORES["multiple_h1"]["impact"],
                    "effort": self.ISSUE_SCORES["multiple_h1"]["effort"],
                    "priority_score": self.ISSUE_SCORES["multiple_h1"]["impact"] / self.ISSUE_SCORES["multiple_h1"]["effort"],
                    "recommendation": "Use a single H1 tag per page to maintain clear content hierarchy"
                }
                self.issues["low"].append(issue)
    
    def run_analysis(self):
        """Run all analysis methods"""
        # Critical issues
        self.analyze_broken_links()
        self.analyze_redirect_chains()
        self.analyze_duplicate_titles()
        
        # High priority issues
        self.analyze_missing_meta_descriptions()
        self.analyze_missing_h1()
        self.analyze_slow_pages()
        
        # Medium priority issues
        self.analyze_title_length()
        self.analyze_description_length()
        self.analyze_missing_alt_text()
        
        # Low priority issues
        self.analyze_multiple_h1()
        
        # Sort issues by priority score
        for category in self.issues:
            self.issues[category] = sorted(
                self.issues[category], 
                key=lambda x: x.get("priority_score", 0), 
                reverse=True
            )
        
        # Calculate summary
        self.summary = {
            "total_issues": sum(len(issues) for issues in self.issues.values()),
            "critical_count": len(self.issues["critical"]),
            "high_count": len(self.issues["high"]),
            "medium_count": len(self.issues["medium"]),
            "low_count": len(self.issues["low"]),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "highest_impact_issues": self._get_highest_impact_issues(3)
        }
    
    def _get_highest_impact_issues(self, n=3):
        """Get the n highest impact issues across all categories"""
        all_issues = []
        for category, issues in self.issues.items():
            all_issues.extend(issues)
        
        # Sort by impact score
        sorted_issues = sorted(all_issues, key=lambda x: x.get("impact", 0), reverse=True)
        
        return sorted_issues[:n]
    
    def generate_report(self, output_dir="reports"):
        """Generate JSON report with all findings"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"seo_audit_report_{timestamp}.json")
        
        # Create report data
        report = {
            "summary": self.summary,
            "issues": self.issues
        }
        
        # Write report to file
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        
        print(f"Report generated: {report_file}")
        return report_file
    
    def generate_charts(self, output_dir="reports"):
        """Generate visualizations of the audit results"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        charts_file = os.path.join(output_dir, f"seo_audit_charts_{timestamp}.png")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # Issues by priority category
        categories = ["Critical", "High", "Medium", "Low"]
        counts = [
            self.summary["critical_count"],
            self.summary["high_count"],
            self.summary["medium_count"],
            self.summary["low_count"]
        ]
        
        # Plot issues by category
        bars = axes[0].bar(categories, counts, color=['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c'])
        axes[0].set_title('SEO Issues by Priority Category')
        axes[0].set_ylabel('Number of Issues')
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[0].annotate(f'{height}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),
                         textcoords="offset points",
                         ha='center', va='bottom')
        
        # Plot top issues by impact
        if self.summary["highest_impact_issues"]:
            top_issues = self.summary["highest_impact_issues"]
            titles = [issue["title"] for issue in top_issues]
            impacts = [issue["impact"] for issue in top_issues]
            efforts = [issue["effort"] for issue in top_issues]
            
            x = np.arange(len(titles))
            width = 0.35
            
            axes[1].bar(x - width/2, impacts, width, label='Impact (1-10)', color='#337ab7')
            axes[1].bar(x + width/2, efforts, width, label='Effort (1-10)', color='#5cb85c')
            
            axes[1].set_title('Top Issues by Impact')
            axes[1].set_ylabel('Score')
            axes[1].set_xticks(x)
            axes[1].set_xticklabels(titles, rotation=45, ha='right')
            axes[1].legend()
        
        plt.tight_layout()
        plt.savefig(charts_file)
        plt.close()
        
        print(f"Charts generated: {charts_file}")
        return charts_file
    
    def generate_html_report(self, output_dir="reports"):
        """Generate HTML report with all findings"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"seo_audit_report_{timestamp}.html")
        
        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SEO Audit Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                h2 { color: #3498db; margin-top: 30px; }
                h3 { color: #2c3e50; }
                .summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
                .summary-item { text-align: center; padding: 15px; border-radius: 5px; }
                .critical { background-color: #f8d7da; color: #721c24; }
                .high { background-color: #fff3cd; color: #856404; }
                .medium { background-color: #d1ecf1; color: #0c5460; }
                .low { background-color: #d4edda; color: #155724; }
                .issue { margin-bottom: 30px; padding: 15px; border-radius: 5px; border-left: 5px solid #ddd; }
                .issue.critical { border-left-color: #dc3545; }
                .issue.high { border-left-color: #ffc107; }
                .issue.medium { border-left-color: #17a2b8; }
                .issue.low { border-left-color: #28a745; }
                .score-bar { display: flex; margin: 10px 0; }
                .score-impact, .score-effort { height: 20px; color: white; text-align: center; line-height: 20px; }
                .score-impact { background-color: #007bff; }
                .score-effort { background-color: #28a745; }
                .examples { background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; overflow-x: auto; }
                .examples code { white-space: nowrap; }
                footer { margin-top: 30px; text-align: center; color: #6c757d; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Technical SEO Audit Report</h1>
                <p>Generated on: {date}</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <div class="summary-grid">
                        <div class="summary-item critical">
                            <h3>Critical Issues</h3>
                            <p>{critical_count}</p>
                        </div>
                        <div class="summary-item high">
                            <h3>High Priority</h3>
                            <p>{high_count}</p>
                        </div>
                        <div class="summary-item medium">
                            <h3>Medium Priority</h3>
                            <p>{medium_count}</p>
                        </div>
                        <div class="summary-item low">
                            <h3>Low Priority</h3>
                            <p>{low_count}</p>
                        </div>
                    </div>
                </div>
                
                {issues_html}
                
                <footer>
                    <p>This report was automatically generated by SEO Audit Automation Tool</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        # Generate issues HTML
        issues_html = ""
        
        # Categories in order
        categories = [
            ("critical", "Critical Issues"),
            ("high", "High Priority Issues"),
            ("medium", "Medium Priority Issues"),
            ("low", "Low Priority Issues")
        ]
        
        for category_key, category_title in categories:
            if self.issues[category_key]:
                issues_html += f"<h2>{category_title}</h2>\n"
                
                for issue in self.issues[category_key]:
                    issues_html += f"""
                    <div class="issue {category_key}">
                        <h3>{issue["title"]} ({issue["count"]} instances)</h3>
                        <p>{issue["description"]}</p>
                        
                        <div class="score-bar">
                            <div class="score-impact" style="width: {issue["impact"]*10}%;">Impact: {issue["impact"]}/10</div>
                        </div>
                        <div class="score-bar">
                            <div class="score-effort" style="width: {issue["effort"]*10}%;">Effort: {issue["effort"]}/10</div>
                        </div>
                        
                        <h4>Recommendation:</h4>
                        <p>{issue["recommendation"]}</p>
                        
                        <h4>Examples:</h4>
                        <div class="examples">
                            <code>{"<br>".join(issue["examples"])}</code>
                        </div>
                    </div>
                    """
        
        # Render the template
        html_content = html_template.format(
            date=self.summary["date"],
            critical_count=self.summary["critical_count"],
            high_count=self.summary["high_count"],
            medium_count=self.summary["medium_count"],
            low_count=self.summary["low_count"],
            issues_html=issues_html
        )
        
        # Write to file
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"HTML report generated: {report_file}")
        return report_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automate SEO audit from Screaming Frog exports")
    parser.add_argument("export_dir", help="Directory containing Screaming Frog export files")
    parser.add_argument("--output", default="reports", help="Output directory for reports")
    args = parser.parse_args()
    
    # Create automation instance
    audit = SEOAuditAutomation(args.export_dir)
    
    # Load files
    if not audit.load_files():
        print("Failed to load files. Exiting.")
        exit(1)
    
    # Run analysis
    audit.run_analysis()
    
    # Generate reports
    audit.generate_report(args.output)
    audit.generate_charts(args.output)
    audit.generate_html_report(args.output)
    
    print("SEO audit completed successfully!")