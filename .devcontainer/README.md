# Dev Container Configuration

This directory contains the development container configuration for the **Real-Time Intelligence for Operations** solution accelerator.

## What is a Dev Container?

A development container (or dev container for short) allows you to use a container as a full-featured development environment. This dev container is configured with all the tools and dependencies needed to work with this project.

## Features Included

### Core Tools
- **Python 3.14** with pip and venv
- **Azure CLI** with Bicep extension
- **Azure Developer CLI (azd)**
- **PowerShell** (for cross-platform script execution)
- **Git** and **GitHub CLI**

### Python Development
- **Jupyter Lab** for notebook development
- **Black** code formatter
- **Flake8** linter
- **Pylance** language server
- **pytest** testing framework
- **mypy** type checker
- **Bandit** security linter

### VS Code Extensions
- GitHub Copilot and Copilot Chat
- Python development extensions (Python, Pylance, Black formatter)
- Azure tooling extensions (Azure CLI, Bicep, Azure Developer CLI)
- Jupyter notebook support with cell tags and slideshow
- GitHub Actions
- PowerShell extension
- YAML and JSON support

## Getting Started

### Prerequisites
- [Visual Studio Code](https://code.visualstudio.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Using the Dev Container

1. **Open in Dev Container**:
   - Open this repository in VS Code
   - Press `F1` or `Ctrl+Shift+P` to open the command palette
   - Type "Dev Containers: Reopen in Container" and select it
   - VS Code will build and start the dev container

2. **Alternative Methods**:
   - **GitHub Codespaces**: Click the "Code" button in GitHub → Codespaces → Create codespace
   - **Command Line**: Use `code .` in the repository root with the Dev Containers extension installed

### First Time Setup

After the container starts, configure Git and authenticate with Azure:

```bash
# Configure Git (required for commits)
git config --global user.name "Your Name"
git config --global user.email "your-email@domain.com"

# Authenticate with Azure CLI
az login

# Authenticate with Azure Developer CLI
azd auth login

# Recommended: set email to receive alerts
azd env set FABRIC_ACTIVATOR_ALERTS_EMAIL "myteam@company.com"

# Optional: Customize resource names
azd env set FABRIC_WORKSPACE_NAME "My RTI Workspace"

# Deploy the solution
azd up
```

## Container Configuration

The dev container includes:

- **Base Image**: Microsoft's Python 3.14 dev container (Debian Trixie)
- **Mounted Volumes**: Your local `.azure` directory for persistent authentication
- **Port Forwarding**: Ports 8000, 8080, and 8888 for web applications
- **Post-Create Script**: Automatically installs project dependencies and development tools

## Development Workflow

1. **Code Development**: Use VS Code with full IntelliSense and debugging support
2. **Testing**: Run `pytest` for unit tests
3. **Formatting**: Code is auto-formatted with Black on save
4. **Security Scanning**: Use `bandit` to scan for security issues
5. **Deployment**: Use `azd up` to deploy to Azure
6. **Event Simulation**: Use `python infra/scripts/event_simulator.py` to generate real-time telemetry data
7. **Data Ingestion**: Use `python infra/scripts/fabric/fabric_data_ingester.py` for batch data operations
8. **Notebooks**: Use `jupyter lab` for interactive development

## Troubleshooting

### Container Won't Start
- Ensure Docker Desktop is running
- Check that you have the Dev Containers extension installed
- Try rebuilding the container: Command Palette → "Dev Containers: Rebuild Container"

### Authentication Issues
- Your Azure credentials are mounted from `~/.azure` on your host machine
- If you get authentication errors, try `az login` again inside the container

### Permission Issues on Windows
- Ensure Docker Desktop has access to your drives
- Check Windows Subsystem for Linux (WSL) integration if using WSL

## Customization

You can customize the dev container by:

1. **Adding Extensions**: Edit `devcontainer.json` → `customizations.vscode.extensions`
2. **Installing Packages**: Modify `post-create.sh` script
3. **Environment Variables**: Add to `containerEnv` in `devcontainer.json`
4. **Port Forwarding**: Update `forwardPorts` array

## Benefits

✅ **Consistent Environment**: Same development environment for all team members  
✅ **Quick Setup**: Zero manual installation of tools and dependencies  
✅ **Isolated**: Container doesn't affect your host machine  
✅ **Pre-configured**: Ready to use with all necessary tools  
✅ **Cloud-ready**: Works with GitHub Codespaces  
✅ **Latest Python**: Uses Python 3.14 with all modern features  
✅ **Azure-optimized**: Pre-configured for Microsoft Fabric and Azure services  

---

For more information about dev containers, visit the [official documentation](https://containers.dev/).

## Installed Python Packages

The dev container comes with the following Python packages pre-installed:

### Azure SDK Libraries
- `azure-identity` - Authentication for Azure services
- `azure-core` - Core Azure SDK functionality
- `azure-storage-file-datalake` - OneLake and Data Lake Storage operations
- `azure-mgmt-eventhub` - Event Hub management
- `azure-kusto-data` - Kusto/KQL database connections
- `azure-kusto-ingest` - Data ingestion to Kusto databases
- `azure-eventhub` - Event Hub client for sending events

### Data Processing & Utilities
- `pandas` - Data manipulation and analysis
- `requests` - HTTP API calls
- `python-dateutil` - Date/time utilities

### Development Tools
- `black` - Code formatter
- `flake8` - Linter
- `pytest` - Testing framework
- `mypy` - Type checker
- `bandit` - Security linter
- `jupyter` & `jupyterlab` - Interactive notebooks
- `ipykernel` - Jupyter kernel support