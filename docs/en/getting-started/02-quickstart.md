# Quick Start

Get started with AtomCtx in 5 minutes.

## Prerequisites

Before using AtomCtx, ensure your environment meets the following requirements:

- **Python Version**: 3.10 or higher
- **Operating System**: Linux, macOS, Windows
- **Network Connection**: Stable network connection required (for downloading dependencies and accessing model services)

## Installation & Startup

AtomCtx can be installed via a Python Package to be used as a local library, or you can quickly launch it as an independent service using Docker.

### Option 1: Install via pip (As a local library)

```bash
pip install atom-ctx --upgrade --force-reinstall
```

### Option 2: Start via Docker (As an independent service)

If you prefer to run AtomCtx as a standalone service, Docker is recommended.

1. **Prepare Configuration and Data Directories**
   Create a data directory on your host machine and prepare the `ctx.conf` configuration file (see the "Configuration" section below for details):
   ```bash
   mkdir -p ~/.ctx/data
   touch ~/.ctx/ctx.conf
   ```

2. **Start with Docker Compose**
   Create a `docker-compose.yml` file:
   ```yaml
   services:
     atom_ctx:
       image: ghcr.io/volcengine/atom_ctx:main
       container_name: atom_ctx
       ports:
         - "1933:1933"
       volumes:
         - ~/.ctx/ctx.conf:/app/ctx.conf
         - ~/.ctx/data:/app/data
       restart: unless-stopped
   ```
   Then run the following command in the same directory:
   ```bash
   docker-compose up -d
   ```

> **💡 Mac Local Network Access Tip (Connection reset error):**
>
> By default, AtomCtx only listens to `127.0.0.1` for security reasons. If you are using Docker on a Mac, your host machine may not be able to access it directly via `localhost:1933`.
> 
> **Recommended Solution: Use socat for port forwarding (No config changes needed):**
> Override the default startup command in your `docker-compose.yml` to use `socat` for internal port forwarding:
> ```yaml
> services:
>   atom_ctx:
>     image: ghcr.io/volcengine/atom_ctx:main
>     ports:
>       - "1933:1934" # Map host 1933 to container 1934
>     volumes:
>       - ~/.ctx/ctx.conf:/app/ctx.conf
>       - ~/.ctx/data:/app/data
>     command: /bin/sh -c "apt-get update && apt-get install -y socat && socat TCP-LISTEN:1934,fork,reuseaddr TCP:127.0.0.1:1933 & ctx-server"
> ```
> This perfectly solves the access issue for Mac host machines.

## Model Preparation

AtomCtx requires the following model capabilities:
- **VLM Model**: For image and content understanding
- **Embedding Model**: For vectorization and semantic retrieval

AtomCtx supports multiple model services:
- **Volcengine (Doubao Models)**: Recommended, cost-effective with good performance, free quota for new users. For purchase and activation, see: [Volcengine Purchase Guide](../guides/02-volcengine-purchase-guide.md)
- **OpenAI Models**: Supports GPT-4V and other VLM models, plus OpenAI Embedding models
- **Other Custom Model Services**: Supports model services compatible with OpenAI API format

## Configuration

### Configuration File Template

Create a configuration file `~/.ctx/ctx.conf`:

```json
{
  "embedding": {
    "dense": {
      "api_base" : "<api-endpoint>",
      "api_key"  : "<your-api-key>",
      "provider" : "<provider-type>",
      "dimension": 1024,
      "model"    : "<model-name>"
    }
  },
  "vlm": {
    "api_base" : "<api-endpoint>",
    "api_key"  : "<your-api-key>",
    "provider" : "<provider-type>",
    "model"    : "<model-name>"
  }
}
```

For complete examples for each model provider, see [Configuration Guide - Examples](../guides/01-configuration.md#configuration-examples).

### Environment Variables

When the config file is at the default path `~/.ctx/ctx.conf`, no additional setup is needed — AtomCtx loads it automatically.

If the config file is at a different location, specify it via environment variable:

```bash
export CTX_CONFIG_FILE=/path/to/your/ctx.conf
```

## Run Your First Example

### Create Python Script

Create `example.py`:

```python
import atom_ctx as ctx

# Initialize AtomCtx client with data directory
client = ctx.AtomCtx(path="./data")

try:
    # Initialize the client
    client.initialize()

    # Add resource (supports URL, file, or directory)
    add_result = client.add_resource(
        path="https://raw.githubusercontent.com/volcengine/AtomCtx/refs/heads/main/README.md"
    )
    root_uri = add_result['root_uri']

    # Explore the resource tree structure
    ls_result = client.ls(root_uri)
    print(f"Directory structure:\n{ls_result}\n")

    # Use glob to find markdown files
    glob_result = client.glob(pattern="**/*.md", uri=root_uri)
    if glob_result['matches']:
        content = client.read(glob_result['matches'][0])
        print(f"Content preview: {content[:200]}...\n")

    # Wait for semantic processing to complete
    print("Wait for semantic processing...")
    client.wait_processed()

    # Get abstract and overview of the resource
    abstract = client.abstract(root_uri)
    overview = client.overview(root_uri)
    print(f"Abstract:\n{abstract}\n\nOverview:\n{overview}\n")

    # Perform semantic search
    results = client.find("what is atom_ctx", target_uri=root_uri)
    print("Search results:")
    for r in results.resources:
        print(f"  {r.uri} (score: {r.score:.4f})")

    # Close the client
    client.close()

except Exception as e:
    print(f"Error: {e}")
```

### Run the Script

```bash
python example.py
```

### Expected Output

```
Directory structure:
...

Content preview: ...

Wait for semantic processing...
Abstract:
...

Overview:
...

Search results:
  ctx://resources/... (score: 0.8523)
  ...
```

Congratulations! You have successfully run AtomCtx.

## Server Mode

Want to run AtomCtx as a shared service? See [Quick Start: Server Mode](03-quickstart-server.md).

## Next Steps

- [Configuration Guide](../guides/01-configuration.md) - Detailed configuration options
- [API Overview](../api/01-overview.md) - API reference
- [Resource Management](../api/02-resources.md) - Resource management API
