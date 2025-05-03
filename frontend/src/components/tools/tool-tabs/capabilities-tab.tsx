// src/components/tools/tool-tabs/capabilities-tab.tsx
import React from 'react';
import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Terminal } from 'lucide-react';
import { CodeBlock, atomOneDark } from 'react-code-blocks';

import { Tool } from '../tool-detail';

interface ToolCapabilitiesTabProps {
  tool: Tool;
  toolId: string;
  router: AppRouterInstance;
}

export function ToolCapabilitiesTab({ tool, toolId, router }: ToolCapabilitiesTabProps) {
  // Format parameter type
  const formatParameterType = (type: string) => {
    switch (type) {
      case 'string':
        return 'String';
      case 'number':
        return 'Number';
      case 'boolean':
        return 'Boolean';
      case 'array':
        return 'Array';
      case 'object':
        return 'Object';
      default:
        return type;
    }
  };

  // Generate example code for calling the tool
  const generateExampleCode = (capability: Tool['capabilities'][0]) => {
    const paramValues: Record<string, any> = {};
    
    // Generate example values for parameters
    Object.entries(capability.parameters).forEach(([key, param]) => {
      if (param.type === 'string') {
        paramValues[key] = param.example || 'example_string';
      } else if (param.type === 'number') {
        paramValues[key] = param.example || 42;
      } else if (param.type === 'boolean') {
        paramValues[key] = param.example || true;
      } else if (param.type === 'array') {
        paramValues[key] = param.example || [1, 2, 3];
      } else if (param.type === 'object') {
        paramValues[key] = param.example || { key: 'value' };
      }
    });
    
    const code = `// Example: Calling the ${capability.name} capability
import { callMcpTool } from '@/lib/mcp/client';

// Call the tool
const result = await callMcpTool(
  '${tool?.mcp_endpoint || '[MCP_ENDPOINT]'}',
  '${capability.name}',
  ${JSON.stringify(paramValues, null, 2)}
);

// Process the result
console.log(result);`;
    
    return code;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tool Capabilities</CardTitle>
        <CardDescription>
          This tool provides the following capabilities
        </CardDescription>
      </CardHeader>
      <CardContent>
        {tool.capabilities.length === 0 ? (
          <div className="text-center p-12 border border-dashed rounded-lg">
            <h3 className="font-medium text-lg mb-2">No capabilities defined</h3>
            <p className="text-gray-500 mb-4">
              This tool doesn't have any capabilities defined.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {tool.capabilities.map((capability) => (
              <div 
                key={capability.name} 
                className="border rounded-lg overflow-hidden"
              >
                <div className="p-4 bg-gray-50 border-b flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{capability.name}</h3>
                    <p className="text-sm text-gray-500">
                      {capability.description}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => router.push(`/tools/${toolId}/call/${capability.name}`)}
                  >
                    <Terminal className="mr-2 h-4 w-4" />
                    Call
                  </Button>
                </div>
                <div className="p-4">
                  <h4 className="text-sm font-medium mb-2">Parameters</h4>
                  {Object.keys(capability.parameters).length === 0 ? (
                    <p className="text-sm text-gray-500">No parameters required</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Name
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Type
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Description
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Required
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {Object.entries(capability.parameters).map(([name, param]: [string, any]) => (
                            <tr key={name}>
                              <td className="px-4 py-2 text-sm">
                                <code className="bg-gray-100 px-1 py-0.5 rounded">
                                  {name}
                                </code>
                              </td>
                              <td className="px-4 py-2 text-sm">
                                {formatParameterType(param.type)}
                              </td>
                              <td className="px-4 py-2 text-sm">
                                {param.description || '-'}
                              </td>
                              <td className="px-4 py-2 text-sm">
                                {param.required ? 'Yes' : 'No'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
                {capability.returns && (
                  <div className="p-4 border-t">
                    <h4 className="text-sm font-medium mb-2">Returns</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Type
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Description
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          <tr>
                            <td className="px-4 py-2 text-sm">
                              {formatParameterType(capability.returns.type)}
                            </td>
                            <td className="px-4 py-2 text-sm">
                              {capability.returns.description || '-'}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                <div className="p-4 border-t">
                  <h4 className="text-sm font-medium mb-2">Example Code</h4>
                  <div className="bg-gray-900 rounded-md overflow-hidden">
                    <CodeBlock
                      text={generateExampleCode(capability)}
                      language="javascript"
                      showLineNumbers={true}
                      theme={atomOneDark}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}