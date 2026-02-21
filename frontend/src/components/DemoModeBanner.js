import React from 'react';
import { Eye, EyeOff, Info } from 'lucide-react';
import { Button } from './ui/button';
import { useDemoMode } from '../contexts/DemoModeContext';

export default function DemoModeBanner() {
  const { demoMode, toggleDemoMode } = useDemoMode();

  if (!demoMode) return null;

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 bg-amber-100 rounded-lg">
              <Eye className="w-4 h-4 text-amber-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-900">
                Demo Mode Active
              </p>
              <p className="text-xs text-amber-700">
                You're viewing sample data. Your real data is safe.
              </p>
            </div>
          </div>
          <Button
            onClick={toggleDemoMode}
            variant="outline"
            size="sm"
            className="border-amber-300 text-amber-700 hover:bg-amber-100"
          >
            <EyeOff className="w-4 h-4 mr-2" />
            Exit Demo
          </Button>
        </div>
      </div>
    </div>
  );
}
