"""
Run Logger
Centralized logging infrastructure for Factory runs.
Creates structured run logs for CASS indexing.

Usage:
    from run_logger import RunLogger
    
    with RunLogger("intake_packager", {"url": "https://example.com"}) as run:
        run.log("Starting intake...")
        # ... do work ...
        run.set_output("client_slug", slug)
        run.set_output("dossier_path", str(path))
"""
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import io


# Run logs directory
RUNS_DIR = Path(__file__).parent.parent / "runs"


class RunLogger:
    """Context manager for structured run logging."""
    
    def __init__(self, tool_name, args_dict=None):
        self.tool_name = tool_name
        self.args_dict = args_dict or {}
        self.run_id = uuid.uuid4().hex[:12]
        self.start_time = datetime.utcnow()
        self.date_str = self.start_time.strftime("%Y-%m-%d")
        
        # Create run directory
        self.run_dir = RUNS_DIR / self.date_str / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logs
        self.events = []
        self.outputs = {}
        self.errors = []
        self.success = True
        
        # Capture stdout/stderr
        self._stdout_capture = io.StringIO()
        self._stderr_capture = io.StringIO()
        self._original_stdout = None
        self._original_stderr = None
    
    def __enter__(self):
        # Start capturing output (tee to both console and capture)
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = TeeWriter(self._original_stdout, self._stdout_capture)
        sys.stderr = TeeWriter(self._original_stderr, self._stderr_capture)
        
        self.log(f"Run started: {self.tool_name}")
        
        # Check UMCP status (advisory, no-op if not configured)
        self._record_umcp_status()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stdout/stderr
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        
        # Record end time
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        # Handle exceptions
        if exc_type is not None:
            self.success = False
            self.errors.append(f"{exc_type.__name__}: {exc_val}")
            self.log(f"Run failed: {exc_val}")
        else:
            self.log("Run completed successfully")
        
        # Write all logs
        self._write_logs()
        
        # Send Agent Mail notification (advisory, no-op if not configured)
        self._send_agent_mail_notification()
        
        # Don't suppress exceptions
        return False
    
    def log(self, message, level="INFO"):
        """Log an event."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        self.events.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def error(self, message):
        """Log an error."""
        self.errors.append(message)
        self.log(message, level="ERROR")
    
    def set_output(self, key, value):
        """Record an output value."""
        self.outputs[key] = value
    
    def set_input(self, key, value):
        """Add to input args."""
        self.args_dict[key] = value
    
    def _write_logs(self):
        """Write all log files."""
        # 1. Metadata JSON
        metadata = {
            "run_id": self.run_id,
            "tool": self.tool_name,
            "timestamp": self.start_time.isoformat() + "Z",
            "end_time": self.end_time.isoformat() + "Z",
            "duration_seconds": round(self.duration_seconds, 2),
            "success": self.success,
            "command": f"python tools/{self.tool_name}.py",
            "args": self.args_dict,
            "outputs": self.outputs,
            "errors": self.errors
        }
        
        with open(self.run_dir / "run_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # 2. Stdout log
        stdout_content = self._stdout_capture.getvalue()
        with open(self.run_dir / "run_stdout.log", 'w', encoding='utf-8') as f:
            f.write(stdout_content)
        
        # 3. Stderr log
        stderr_content = self._stderr_capture.getvalue()
        with open(self.run_dir / "run_stderr.log", 'w', encoding='utf-8') as f:
            f.write(stderr_content)
        
        # 4. Summary markdown
        summary = self._generate_summary()
        with open(self.run_dir / "run_summary.md", 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def _generate_summary(self):
        """Generate human-readable summary."""
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        
        summary = f"""# Run Summary: {self.run_id}

**Tool:** {self.tool_name}
**Status:** {status}
**Started:** {self.start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC
**Duration:** {self.duration_seconds:.1f}s

## Inputs
"""
        for k, v in self.args_dict.items():
            summary += f"- **{k}:** {v}\n"
        
        summary += "\n## Outputs\n"
        for k, v in self.outputs.items():
            summary += f"- **{k}:** {v}\n"
        
        if self.errors:
            summary += "\n## Errors\n"
            for err in self.errors:
                summary += f"- {err}\n"
        
        summary += f"\n---\n_Run ID: {self.run_id}_\n"
        return summary
    
    def _send_agent_mail_notification(self):
        """Send advisory notification to Agent Mail (if configured)."""
        try:
            from agent_mail_client import notify_build_complete, notify_failure
            
            if self.success:
                # Notify build complete
                client_slug = self.outputs.get("client_slug", "unknown")
                artifacts = list(self.outputs.keys())
                manifest_hash = self.outputs.get("manifest_hash", "")
                notify_build_complete(client_slug, artifacts, manifest_hash)
            else:
                # Notify failure
                error = self.errors[0] if self.errors else "Unknown error"
                notify_failure(self.run_id, error, self.tool_name)
        except ImportError:
            pass  # Agent mail client not available
        except Exception:
            pass  # Silently fail - advisory only
    
    def _record_umcp_status(self):
        """Record UMCP Tool Bus status (advisory, no-op if not configured)."""
        try:
            from umcp_client import get_umcp_status
            
            status = get_umcp_status()
            if status.get("connected"):
                self.log(f"UMCP connected: {status['tool_count']} tools, namespaces: {status.get('namespaces', [])}")
                self.set_output("umcp_connected", True)
                self.set_output("umcp_tool_count", status['tool_count'])
        except ImportError:
            pass  # UMCP client not available
        except Exception:
            pass  # Silently fail - advisory only


class TeeWriter:
    """Write to multiple streams simultaneously."""
    
    def __init__(self, *streams):
        self.streams = streams
    
    def write(self, data):
        for stream in self.streams:
            try:
                stream.write(data)
            except:
                pass
    
    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except:
                pass
    
    def reconfigure(self, **kwargs):
        """Support reconfigure for stdout."""
        for stream in self.streams:
            if hasattr(stream, 'reconfigure'):
                try:
                    stream.reconfigure(**kwargs)
                except:
                    pass
