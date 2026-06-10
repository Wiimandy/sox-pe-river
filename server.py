import http.server
import socketserver
import json
import subprocess
import sys
import os

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Initialize SimpleHTTPRequestHandler serving DIRECTORY
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/refresh' or self.path == '/api/export-charts':
            is_export = (self.path == '/api/export-charts')
            action_name = "chart export" if is_export else "data refresh"
            
            print("\n" + "="*50)
            print(f"  API: Received {action_name} request from frontend")
            print("="*50)
            
            success = True
            log_messages = []
            
            # Helper to run scripts
            def run_script(script_name):
                cmd = [sys.executable, script_name]
                print(f"Running: {' '.join(cmd)}")
                log_messages.append(f"Running {script_name}...")
                
                # Run with UTF-8 encoding environment variable
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                res = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    env=env,
                    cwd=DIRECTORY
                )
                if res.returncode == 0:
                    print(f"  -> SUCCESS")
                    log_messages.append(f"✅ {script_name} completed successfully.")
                    return True, res.stdout
                else:
                    print(f"  -> FAILED with exit code {res.returncode}")
                    print(res.stderr)
                    log_messages.append(f"❌ {script_name} failed (Exit Code {res.returncode}):")
                    log_messages.append(res.stderr)
                    return False, res.stderr

            if is_export:
                # For chart export:
                # 1. Run plot_river.py to generate fresh 5-year trend charts
                ok, out = run_script("plot_river.py")
                if not ok:
                    success = False
                
                # 2. Run export_charts.py to copy to OneDrive
                if success:
                    ok, out = run_script("export_charts.py")
                    if not ok:
                        success = False
            else:
                # For data refresh:
                # 1. Run query_all.py
                ok, out = run_script("query_all.py")
                if not ok:
                    success = False
                    
                # 2. Run plot_river.py
                if success:
                    ok, out = run_script("plot_river.py")
                    if not ok:
                        success = False
                        
                # 3. Run compile_data.py
                if success:
                    ok, out = run_script("compile_data.py")
                    if not ok:
                        success = False

            # Prepare response
            response_data = {
                "status": "success" if success else "error",
                "logs": "\n".join(log_messages)
            }
            
            response_bytes = json.dumps(response_data).encode('utf-8')
            
            self.send_response(200 if success else 500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_bytes)))
            # Enable CORS
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_bytes)
            print("="*50 + "\n")
        else:
            self.send_error(404, "File not found")

    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    # Change working directory to this file's folder to prevent path issues
    os.chdir(DIRECTORY)
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print("="*60)
        print(f"  SOX Index River Chart Local Web Server")
        print(f"  Serving at: http://localhost:{PORT}")
        print(f"  Serving directory: {DIRECTORY}")
        print(f"  Press Ctrl+C to stop the server.")
        print("="*60)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.server_close()
            print("Server stopped.")

if __name__ == "__main__":
    main()
