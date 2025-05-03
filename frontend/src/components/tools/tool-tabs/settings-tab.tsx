// src/components/tools/tool-tabs/settings-tab.tsx
import React from 'react';
import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import {
  Edit,
  Trash2
} from 'lucide-react';

import { Tool } from '../tool-detail';

interface ToolSettingsTabProps {
  tool: Tool;
  toolId: string;
  router: AppRouterInstance;
  onUnregister: () => void;
  isUnregistering: boolean;
}

export function ToolSettingsTab({ 
  tool, 
  toolId, 
  router, 
  onUnregister,
  isUnregistering 
}: ToolSettingsTabProps) {
  return (
    <div className="space-y-4">