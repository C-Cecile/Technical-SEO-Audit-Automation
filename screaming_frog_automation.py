import os
import subprocess
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("screaming_frog_automation.log"),
        logging.StreamHandler()
    ]
)

class ScreamingFrogAutomation:
    """
    A class to automate Screaming Frog crawls and exports
    """
    
    def __init__(self, sf_path=None):
        """
        Initialize the Screaming Frog automation
        
        Args:
            sf_path (str): Path to the Screaming Frog executable
        """
        # Default paths for different operating systems
        if sf_path is None:
            if os.name == 'nt':  # Windows
                sf_path = r'C:\Program Files\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe'
            elif os.name == 'posix':  # macOS/Linux
                if os.path.exists('/Applications/Screaming Frog SEO Spider.app'):  # macOS
                    sf_path = '/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderCli'
                else:  # Linux
                    sf_path = '/usr/bin/screamingfrogseospider'
        
        self.sf_path = sf_path
        if not os.path.exists(self.sf_path):
            logging.warning(f"Screaming Frog executable not found at {self.sf_path}")
    
    def run_crawl(self, url, output_dir, config_file=None, max_urls=None, crawl_settings=None):
        """
        Run a Screaming Frog crawl and export the results
        
        Args:
            url (str): The URL to crawl
            output_dir (str): Directory to save exports
            config_file (str, optional): Path to Screaming Frog config file
            max_urls (int, optional): Maximum URLs to crawl
            crawl_settings (dict, optional): Additional crawl settings
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command
        cmd = [self.sf_path, '--headless', '--crawl', url, '--output-folder', output_dir]
        
        # Add config file if provided
        if config_file and os.path.exists(config_file):
            cmd.extend(['--config', config_file])
        
        # Add max URLs if provided
        if max_urls:
            cmd.extend(['--bulk-max-urls', str(max_urls)])
        
        # Add additional crawl settings
        if crawl_settings:
            for key, value in crawl_settings.items():
                cmd.extend([f'--{key}', str(value)])
        
        # Start crawl process
        logging.info(f"Starting Screaming Frog crawl of {url}")
        logging.info(f"Command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor and log output
            for line in process.stdout:
                logging.info(line.strip())
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode != 0:
                logging.error(f"Screaming Frog crawl failed with return code {process.returncode}")
                for line in process.stderr:
                    logging.error(line.strip())
                return False
            
            # Check if exports were created
            exports_created = False
            for file in os.listdir(output_dir):
                if file.endswith('.csv'):
                    exports_created = True
                    break
            
            if not exports_created:
                logging.error("No exports were created. Crawl may have failed.")
                return False
            
            logging.info(f"Screaming Frog crawl completed successfully. Exports saved to {output_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Error during Screaming Frog crawl: {str(e)}")
            return False
    
    def run_crawl_with_exports(self, url, output_dir, export_tabs=None, config_file=None):
        """
        Run a Screaming Frog crawl and export specific tabs
        
        Args:
            url (str): The URL to crawl
            output_dir (str): Directory to save exports
            export_tabs (list, optional): List of tabs to export
            config_file (str, optional): Path to Screaming Frog config file
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Default export tabs if none provided
        if export_tabs is None:
            export_tabs = [
                'Internal:All',
                'Internal:HTML',
                'Response Codes',
                'Page Titles',
                'Meta Description',
                'H1',
                'H2',
                'Images',
                'CSS',
                'JavaScript',
                'Directives',
                'Canonicals',
                'Pagination',
                'Hreflang',
                'Structured Data',
                'Redirect Chains',
                'All Inlinks',
                'All Outlinks',
                'Page Speed'
            ]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command
        cmd = [self.sf_path, '--headless', '--crawl', url, '--output-folder', output_dir]
        
        # Add config file if provided
        if config_file and os.path.exists(config_file):
            cmd.extend(['--config', config_file])
        
        # Add export tabs
        for tab in export_tabs:
            cmd.extend(['--export-tabs', tab])
        
        # Start crawl process
        logging.info(f"Starting Screaming Frog crawl of {url} with specific exports")
        logging.info(f"Command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor and log output
            for line in process.stdout:
                logging.info(line.strip())
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode != 0:
                logging.error(f"Screaming Frog crawl failed with return code {process.returncode}")
                for line in process.stderr:
                    logging.error(line.strip())
                return False
            
            # Check if exports were created
            exports_created = False
            for tab in export_tabs:
                tab_name = tab.replace(':', '_').lower()
                found = False
                for file in os.listdir(output_dir):
                    if tab_name in file.lower() and file.endswith('.csv'):
                        found = True
                        exports_created = True
                        break
                if not found:
                    logging.warning(f"Export for tab '{tab}' not found")
            
            if not exports_created:
                logging.error("No exports were created. Crawl may have failed.")
                return False
            
            logging.info(f"Screaming Frog crawl completed successfully. Exports saved to {output_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Error during Screaming Frog crawl: {str(e)}")
            return False
    
    def run_list_crawl(self, url_list_file, output_dir, config_file=None):
        """
        Run a Screaming Frog list crawl using a list of URLs
        
        Args:
            url_list_file (str): Path to a file containing URLs to crawl
            output_dir (str): Directory to save exports
            config_file (str, optional): Path to Screaming Frog config file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(url_list_file):
            logging.error(f"URL list file not found: {url_list_file}")
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command
        cmd = [self.sf_path, '--headless', '--list-crawl', url_list_file, '--output-folder', output_dir]
        
        # Add config file if provided
        if config_file and os.path.exists(config_file):
            cmd.extend(['--config', config_file])
        
        # Start crawl process
        logging.info(f"Starting Screaming Frog list crawl with URLs from {url_list_file}")
        logging.info(f"Command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor and log output
            for line in process.stdout:
                logging.info(line.strip())
            
            # Wait for process to complete
            process.wait()
            
            if process.returncode != 0:
                logging.error(f"Screaming Frog list crawl failed with return code {process.returncode}")
                for line in process.stderr:
                    logging.error(line.strip())
                return False
            
            logging.info(f"Screaming Frog list crawl completed successfully. Exports saved to {output_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Error during Screaming Frog list crawl: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automate Screaming Frog crawls and exports")
    parser.add_argument("--url", help="URL to crawl")
    parser.add_argument("--output-dir", required=True, help="Directory to save exports")
    parser.add_argument("--sf-path", help="Path to Screaming Frog executable")
    parser.add_argument("--config-file", help="Path to Screaming Frog config file")
    parser.add_argument("--max-urls", type=int, help="Maximum URLs to crawl")
    parser.add_argument("--url-list", help="Path to a file containing URLs to crawl")
    
    args = parser.parse_args()
    
    sf = ScreamingFrogAutomation(args.sf_path)
    
    if args.url_list:
        sf.run_list_crawl(args.url_list, args.output_dir, args.config_file)
    elif args.url:
        sf.run_crawl(args.url, args.output_dir, args.config_file, args.max_urls)
    else:
        logging.error("Either --url or --url-list must be provided")