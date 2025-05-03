# OMEGA UI ✨

A modern UI for the **Orchestrated Multi-Expert Gen Agents (OMEGA)** Framework.

![OMEGA Framework Banner](https://via.placeholder.com/1200x300/1E40AF/FFFFFF?text=OMEGA+Framework)

## 🌟 Overview

OMEGA UI is a Next.js-based administration interface for the OMEGA Framework. It provides a comprehensive set of tools for managing AI agents, tools, and workflows. The UI integrates with the Model Context Protocol (MCP) to enable seamless communication between components.

Built with:
- ⚡ **Next.js 14** with App Router
- 🎨 **Tailwind CSS** for styling
- 🧩 **shadcn/ui** components
- 🔄 **React Query** for server state management
- 📊 **D3.js** for visualizations
- 🔌 **MCP Client** for agent/tool communication

## 🚀 Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/omega-ui.git
   cd omega-ui
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Set up environment variables:
   ```bash
   npm run setup-env
   # or
   yarn setup-env
   ```

4. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## 🧠 Key Features

- **Dashboard**: Real-time overview of your OMEGA ecosystem
- **Agent Management**: Create, configure, and monitor agents
- **Tool Registry**: Register, discover, and call MCP tools
- **Workflow Builder**: Visual workflow creator and executor
- **Network Visualization**: Interactive graph of your agent network
- **System Monitoring**: Performance metrics and health checks

## 📂 Project Structure

The project follows a modular structure with separate directories for components, hooks, and API clients:

```
/src
  /app             # Next.js App Router pages
  /components      # Reusable UI components
  /hooks           # Custom React hooks
  /lib             # Utility functions and API clients
  /providers       # React context providers
  /types           # TypeScript type definitions
```

## 🔌 MCP Integration

OMEGA UI integrates with the Model Context Protocol (MCP) for seamless communication with the OMEGA Framework backend. The MCP client in `/src/lib/mcp` provides:

- **Tool Discovery**: Find available tools and their capabilities
- **Tool Execution**: Call tools with parameters and receive results
- **Agent Communication**: Send messages and tasks to agents
- **Resource Management**: Access and manage MCP resources

For more information, see the [MCP Integration Guide](./docs/mcp-integration.md).

## 🖼️ UI Components

The UI is built using shadcn/ui components, which are accessible, customizable React components based on Radix UI primitives. These components can be found in `/src/components/ui`.

Custom OMEGA-specific components are organized by functionality:

- `/src/components/layout`: Layout components (sidebar, header, etc.)
- `/src/components/agents`: Agent-related components
- `/src/components/tools`: Tool-related components
- `/src/components/workflows`: Workflow-related components
- `/src/components/visualizations`: Data visualization components

## 🤝 Contributing

We welcome contributions to the OMEGA UI! Please see our [Contributing Guide](./CONTRIBUTING.md) for more information.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🌐 Related Projects

- [OMEGA Framework](https://github.com/yourusername/omega-framework): The core OMEGA Framework
- [OMEGA Tools](https://github.com/yourusername/omega-tools): Collection of MCP tools for OMEGA
- [OMEGA Examples](https://github.com/yourusername/omega-examples): Example workflows and use cases

## ✨ Acknowledgements

- The OMEGA Framework team
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Model Context Protocol](https://github.com/modelcontextprotocol/modelcontextprotocol)
