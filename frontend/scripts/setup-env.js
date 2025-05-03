// Setup environment variables
const fs = require("fs");
const path = require("path");

// Define environment variables
const envContent = `NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_MCP_REGISTRY_URL=http://localhost:8080/registry
`;

// Write to .env.local file
fs.writeFileSync(path.join(__dirname, "..", ".env.local"), envContent);

console.log("? Environment variables set up successfully!");
