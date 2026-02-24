# Draup Asset Management

A comprehensive IT asset management solution with built-in diagnostic and troubleshooting capabilities, featuring a modern web-based user interface.

## Features

- 🖥️ **Asset Lifecycle**: Track devices and owners
- 🔍 **Diagnostic Tools**: Gather system information and check resources
- 🌐 **Network Tests**: Test network connectivity and diagnose issues
- 💾 **Disk Monitoring**: Check disk usage and alerts
- 🎨 **Modern Web UI**: Beautiful, responsive web interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://127.0.0.1:8080**

## Usage

### Web Interface

The web interface provides:
- **System Health Dashboard**: Real-time health status
- **Agent Metrics**: Performance statistics
- **Task Execution**: Run individual diagnostic tasks
- **Full Diagnostic**: Run all diagnostic checks at once

### Command Line (Alternative)

You can also use the agent programmatically:

```python
from src.agent.it_agent import ITAgent

with ITAgent() as agent:
    # Execute a task
    result = agent.execute_task("system_info")
    print(result)
    
    # Run full diagnostic
    results = agent.diagnose()
    print(results)
    
    # Get health status
    health = agent.get_health_status()
    print(health)
```

## Available Tasks

- **system_info**: Gather system information (OS, CPU, memory, etc.)
- **network_diagnostic**: Test network connectivity to various hosts
- **process_check**: Check if a process is running
- **disk_space_check**: Check disk space usage

## Configuration

Edit `config/config.yaml` to customize:
- Agent settings (name, version, timeouts)
- Logging (level, file location, rotation)
- Monitoring (intervals, health check timeouts)
- Server settings (host, port)

## Project Structure

```
Hackthon-2025/
├── src/
│   ├── agent/
│   │   ├── it_agent.py      # Main agent class
│   │   └── tasks.py          # Task definitions
│   ├── diagnostics/
│   │   ├── health_check.py   # Health monitoring
│   │   ├── logger.py         # Logging system
│   │   └── monitor.py        # Real-time monitoring
│   └── utils/
│       └── config.py         # Configuration management
├── config/
│   └── config.yaml           # Configuration file
├── logs/                     # Log files (auto-created)
├── app.py                    # Web application
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Logs

Logs are automatically stored in `logs/agent.log` with automatic rotation.

## License

This project is created for the Hackathon 2025.

