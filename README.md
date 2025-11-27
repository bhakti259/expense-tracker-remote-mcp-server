# MCP Calculator Server

A remote Model Context Protocol (MCP) server with a calculator tool using SSE transport.

## Features

- **add_numbers**: A tool that adds two numbers together
- Runs as a remote server accessible over HTTP

## Installation

```bash
pip install -e .
```

## Usage

Run the server:

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` and be accessible via SSE transport.

## Connecting to the Server

Configure your MCP client to connect to:

- **URL**: `http://localhost:8000/sse`
- **Transport**: SSE (Server-Sent Events)

## Example

The server exposes an `add_numbers` tool that accepts two numbers (a and b) and returns their sum.
