import requests
import json
import time
import os
import logging

class ScreamingFrogAPI:
    """
    A class to interact with the Screaming Frog API
    Requires a licensed version of Screaming Frog SEO Spider
    """
    
    def __init__(self, api_url="http://localhost:8777"):
        """
        Initialize the Screaming Frog API client
        
        Args:
            api_url (str): URL of the Screaming Frog API (default: http://localhost:8777)
        """
        self.api_url = api_url
        self.headers = {"Content-Type": "application/json"}
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("ScreamingFrogAPI")
    
    def _make_request(self, endpoint, method="GET", data=None, timeout=30):
        """
        Make an HTTP request to the Screaming Frog API
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method (GET, POST, etc.)
            data (dict): Data to send with the request
            timeout (int): Request timeout in seconds
        
        Returns:
            dict: API response
        """
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error: {str(e)}")
            return None
    
    def check_status(self):
        """
        Check if the Screaming Frog API is running
        
        Returns:
            bool: True if API is running, False otherwise
        """
        try:
            response = self._make_request("status")
            return response is not None and response.get("status") == "OK"
        except:
            return False
    
    def start_crawl(self, url, max_urls=None, include_subdomains=False, follow_external_nofollow=False):
        """
        Start a new crawl
        
        Args:
            url (str): URL to crawl
            max_urls (int, optional): Maximum URLs to crawl
            include_subdomains (bool): Whether to include subdomains
            follow_external_nofollow (bool): Whether to follow external nofollow links
        
        Returns:
            str: Crawl ID if successful, None otherwise
        """
        data = {
            "url": url,
            "crawlOptions": {
                "includeSubdomains": include_subdomains,
                "followExternalNofollow": follow_external_nofollow
            }
        }
        
        if max_urls:
            data["crawlOptions"]["maxUrls"] = max_urls
        
        self.logger.info(f"Starting crawl of {url}")
        response = self._make_request("crawl", method="POST", data=data)
        
        if response and "id" in response:
            crawl_id = response["id"]
            self.logger.info(f"Crawl started with ID: {crawl_id}")
            return crawl_id
        else:
            self.logger.error("Failed to start crawl")
            return None
    
    def get_crawl_status(self, crawl_id):
        """
        Get the status of a crawl
        
        Args:
            crawl_id (str): Crawl ID
        
        Returns:
            dict: Crawl status information
        """
        return self._make_request(f"crawl/{crawl_id}")
    
    def wait_for_crawl_completion(self, crawl_id, check_interval=10, timeout=3600):
        """
        Wait for a crawl to complete
        
        Args:
            crawl_id (str): Crawl ID
            check_interval (int): How often to check status (in seconds)
            timeout (int): Maximum time to wait (in seconds)
        
        Returns:
            bool: True if crawl completed successfully, False otherwise
        """
        self.logger.info(f"Waiting for crawl {crawl_id} to complete")
        start_time = time.time()
        
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                self.logger.error(f"Timeout waiting for crawl to complete after {timeout} seconds")
                return False
            
            status = self.get_crawl_status(crawl_id)
            if not status:
                self.logger.error("Failed to get crawl status")
                return False
            
            crawl_status = status.get("status", "")
            urls_crawled = status.get("urlsCrawled", 0)
            
            self.logger.info(f"Crawl status: {crawl_status}, URLs crawled: {urls_crawled}")
            
            if crawl_status == "FINISHED":
                self.logger.info(f"Crawl completed successfully after {int(elapsed_time)} seconds")
                return True
            elif crawl_status in ["FAILED", "STOPPED", "INTERRUPTED"]:
                self.logger.error(f"Crawl failed with status: {crawl_status}")
                return False
            
            time.sleep(check_interval)
    
    def export_crawl(self, crawl_id, export_format="csv", file_path=None, tabs=None):
        """
        Export crawl data
        
        Args:
            crawl_id (str): Crawl ID
            export_format (str): Export format (csv or xlsx)
            file_path (str): Path to save the export
            tabs (list): List of tabs to export
        
        Returns:
            bool: True if export was successful, False otherwise
        """
        if not file_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_path = f"sf_export_{timestamp}.{export_format}"
        
        # Make sure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Default tabs to export if none specified
        if not tabs:
            tabs = [
                "Internal:All",
                "Internal:HTML",
                "Response Codes",
                "Page Titles",
                "Meta Description",
                "H1",
                "Images",
                "Redirect Chains",
                "All Inlinks",
                "Page Speed"
            ]
        
        data = {
            "id": crawl_id,
            "format": export_format,
            "path": file_path,
            "tabs": tabs
        }
        
        self.logger.info(f"Exporting crawl {crawl_id} to {file_path}")
        response = self._make_request("export", method="POST", data=data)
        
        if response and response.get("status") == "OK":
            self.logger.info(f"Export successful")
            return True
        else:
            self.logger.error("Export failed")
            return False
    
    def export_individual_tabs(self, crawl_id, output_dir, export_format="csv"):
        """
        Export individual tabs to separate files
        
        Args:
            crawl_id (str): Crawl ID
            output_dir (str): Directory to save exports
            export_format (str): Export format (csv or xlsx)
        
        Returns:
            bool: True if all exports were successful, False otherwise
        """
        os.makedirs(output_dir, exist_ok=True)
        
        tabs = [
            "Internal:All",
            "Internal:HTML",
            "Response Codes",
            "Page Titles",
            "Meta Description",
            "H1",
            "Images",
            "Redirect Chains",
            "All Inlinks",
            "Page Speed"
        ]
        
        success = True
        for tab in tabs:
            tab_filename = tab.replace(":", "_").replace(" ", "_").lower()
            file_path = os.path.join(output_dir, f"{tab_filename}.{export_format}")
            
            data = {
                "id": crawl_id,
                "format": export_format,
                "path": file_path,
                "tabs": [tab]
            }
            
            self.logger.info(f"Exporting tab {tab} to {file_path}")
            response = self._make_request("export", method="POST", data=data)
            
            if not response or response.get("status") != "OK":
                self.logger.error(f"Failed to export tab {tab}")
                success = False
        
        return success
    
    def run_full_crawl_and_export(self, url, output_dir, max_urls=None, export_format="csv"):
        """
        Run a complete crawl and export workflow
        
        Args:
            url (str): URL to crawl
            output_dir (str): Directory to save exports
            max_urls (int, optional): Maximum URLs to crawl
            export_format (str): Export format (csv or xlsx)
        
        Returns:
            bool: True if the workflow completed successfully, False otherwise
        """
        # Check if API is running
        if not self.check_status():
            self.logger.error("Screaming Frog API is not running or not accessible")
            return False
        
        # Start the crawl
        crawl_id = self.start_crawl(url, max_urls=max_urls)
        if not crawl_id:
            return False
        
        # Wait for crawl to complete
        if not self.wait_for_crawl_completion(crawl_id):
            return False
        
        # Export crawl data
        os.makedirs(output_dir, exist_ok=True)
        return self.export_individual_tabs(crawl_id, output_dir, export_format)


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Interact with Screaming Frog API")
    parser.add_argument("--url", required=True, help="URL to crawl")
    parser.add_argument("--output-dir", required=True, help="Directory to save exports")
    parser.add_argument("--api-url", default="http://localhost:8777", help="Screaming Frog API URL")
    parser.add_argument("--max-urls", type=int, help="Maximum URLs to crawl")
    parser.add_argument("--export-format", default="csv", choices=["csv", "xlsx"], help="Export format")
    
    args = parser.parse_args()
    
    sf_api = ScreamingFrogAPI(args.api_url)
    
    # Make sure Screaming Frog is running with API enabled
    if sf_api.check_status():
        print("Screaming Frog API is running")
        
        # Run a full crawl and export workflow
        success = sf_api.run_full_crawl_and_export(
            url=args.url,
            output_dir=args.output_dir,
            max_urls=args.max_urls,
            export_format=args.export_format
        )
        
        if success:
            print("Crawl and export completed successfully")
        else:
            print("Crawl and export failed")
    else:
        print("Screaming Frog API is not running")
        print("Make sure Screaming Frog is running with the API enabled (licensed version only)")
        print("The API can be enabled in Screaming Frog under Configuration > API > Enable API")