"""
Report templates for different output formats.
"""

from typing import Any, Dict, List


class ReportTemplate:
    """Base class for report templates."""
    
    def render(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError


class JSONReportTemplate(ReportTemplate):
    """JSON report template."""
    
    def render(self, data: Dict[str, Any]) -> str:
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)


class CSVReportTemplate(ReportTemplate):
    """CSV report template (flattened)."""
    
    def render(self, data: Dict[str, Any]) -> str:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Section", "Key", "Value"])
        
        def write_section(section: str, obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    write_section(section, value, f"{prefix}{key}.")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    write_section(section, item, f"{prefix}[{i}].")
            else:
                writer.writerow([section, prefix.rstrip("."), str(obj)])
        
        for section, content in data.items():
            write_section(section, content)
        
        return output.getvalue()


class HTMLReportTemplate(ReportTemplate):
    """HTML report template (for future use)."""
    
    def render(self, data: Dict[str, Any]) -> str:
        html = ["<!DOCTYPE html>", "<html>", "<head>", "<title>NADOS Simulation Report</title>", "</head>", "<body>"]
        html.append("<h1>NADOS Dv1.0 Simulation Report</h1>")
        
        def render_section(section: str, obj: Any, level: int = 2) -> List[str]:
            lines = [f"<h{level}>{section}</h{level}>"]
            if isinstance(obj, dict):
                lines.append("<table border='1'><tr><th>Key</th><th>Value</th></tr>")
                for key, value in obj.items():
                    lines.append(f"<tr><td>{key}</td><td>{self._format_value(value)}</td></tr>")
                lines.append("</table>")
            elif isinstance(obj, list):
                lines.append("<ul>")
                for item in obj:
                    lines.append(f"<li>{self._format_value(item)}</li>")
                lines.append("</ul>")
            else:
                lines.append(f"<p>{obj}</p>")
            return lines
        
        def format_value(val: Any) -> str:
            if isinstance(val, (dict, list)):
                return str(val)
            return str(val)
        
        self._format_value = format_value
        
        for section, content in data.items():
            html.extend(render_section(section, content))
        
        html.extend(["</body>", "</html>"])
        return "\n".join(html)


def get_template(format_type: str) -> ReportTemplate:
    """Get template by format type."""
    templates = {
        "json": JSONReportTemplate,
        "csv": CSVReportTemplate,
        "html": HTMLReportTemplate,
    }
    
    cls = templates.get(format_type.lower())
    if cls is None:
        raise ValueError(f"Unknown template format: {format_type}")
    
    return cls()