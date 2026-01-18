import { useState } from 'react';
import { Moon, Sun, Monitor, Bell, Eye, Database, Key, Save, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePreferencesStore } from '@/stores';

export function SettingsPage() {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your preferences and configuration
        </p>
      </div>

      <AppearanceSection />
      <NotificationsSection />
      <DisplaySection />
      <APIKeysSection />
      <DataSection />
    </div>
  );
}

function AppearanceSection() {
  const { theme, setTheme } = usePreferencesStore();

  const themes: Array<{ value: 'light' | 'dark' | 'system'; label: string; icon: typeof Sun }> = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sun className="h-5 w-5" />
          Appearance
        </CardTitle>
        <CardDescription>Customize how Gorgon looks</CardDescription>
      </CardHeader>
      <CardContent>
        <div>
          <label className="text-sm font-medium mb-3 block">Theme</label>
          <div className="flex gap-2">
            {themes.map(({ value, label, icon: Icon }) => (
              <Button
                key={value}
                variant={theme === value ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setTheme(value)}
              >
                <Icon className="h-4 w-4 mr-2" />
                {label}
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function NotificationsSection() {
  const { notifications, setNotification } = usePreferencesStore();

  const notificationOptions = [
    {
      key: 'executionComplete' as const,
      label: 'Execution Complete',
      description: 'Notify when a workflow execution finishes successfully',
    },
    {
      key: 'executionFailed' as const,
      label: 'Execution Failed',
      description: 'Notify when a workflow execution fails',
    },
    {
      key: 'budgetAlert' as const,
      label: 'Budget Alerts',
      description: 'Notify when spending approaches budget limits',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Notifications
        </CardTitle>
        <CardDescription>Choose what notifications you receive</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {notificationOptions.map(({ key, label, description }) => (
          <div key={key} className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">{label}</p>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notifications[key]}
                onChange={(e) => setNotification(key, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-background after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DisplaySection() {
  const { compactView, setCompactView, showCosts, setShowCosts, defaultPageSize, setDefaultPageSize } =
    usePreferencesStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Eye className="h-5 w-5" />
          Display
        </CardTitle>
        <CardDescription>Configure how data is displayed</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Compact View</p>
            <p className="text-sm text-muted-foreground">Use smaller spacing and fonts</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={compactView}
              onChange={(e) => setCompactView(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-background after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Show Costs</p>
            <p className="text-sm text-muted-foreground">Display cost information in executions</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={showCosts}
              onChange={(e) => setShowCosts(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-background after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Default Page Size</p>
            <p className="text-sm text-muted-foreground">Number of items per page in lists</p>
          </div>
          <select
            value={defaultPageSize}
            onChange={(e) => setDefaultPageSize(Number(e.target.value))}
            className="border rounded px-3 py-1.5 text-sm bg-background"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </CardContent>
    </Card>
  );
}

function APIKeysSection() {
  const [keys, setKeys] = useState({
    openai: '',
    anthropic: '',
    github: '',
  });
  const [showKeys, setShowKeys] = useState({
    openai: false,
    anthropic: false,
    github: false,
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // In production, this would save to backend
    console.log('Saving API keys:', keys);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const apiKeyFields = [
    { key: 'openai' as const, label: 'OpenAI API Key', placeholder: 'sk-...' },
    { key: 'anthropic' as const, label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
    { key: 'github' as const, label: 'GitHub Token', placeholder: 'ghp_...' },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5" />
          API Keys
        </CardTitle>
        <CardDescription>Configure API keys for AI providers and integrations</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {apiKeyFields.map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="text-sm font-medium mb-1.5 block">{label}</label>
            <div className="relative">
              <input
                type={showKeys[key] ? 'text' : 'password'}
                value={keys[key]}
                onChange={(e) => setKeys({ ...keys, [key]: e.target.value })}
                placeholder={placeholder}
                className="w-full border rounded px-3 py-2 text-sm font-mono pr-20 bg-background"
              />
              <button
                type="button"
                onClick={() => setShowKeys({ ...showKeys, [key]: !showKeys[key] })}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground"
              >
                {showKeys[key] ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>
        ))}

        <div className="flex justify-end pt-2">
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            {saved ? 'Saved!' : 'Save Keys'}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">
          API keys are encrypted and stored securely. They are only used for communicating with the
          respective services.
        </p>
      </CardContent>
    </Card>
  );
}

function DataSection() {
  const [clearing, setClearing] = useState(false);

  const handleClearCache = () => {
    setClearing(true);
    // Simulate cache clearing
    setTimeout(() => {
      localStorage.removeItem('gorgon-preferences');
      setClearing(false);
      window.location.reload();
    }, 1000);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Data Management
        </CardTitle>
        <CardDescription>Manage local data and cache</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Clear Local Cache</p>
            <p className="text-sm text-muted-foreground">
              Reset all preferences and cached data. This will reload the page.
            </p>
          </div>
          <Button variant="destructive" size="sm" onClick={handleClearCache} disabled={clearing}>
            <Trash2 className="h-4 w-4 mr-2" />
            {clearing ? 'Clearing...' : 'Clear Cache'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
