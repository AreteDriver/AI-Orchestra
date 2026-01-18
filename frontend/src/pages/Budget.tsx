import {
  Wallet,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Plus,
  Settings,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useBudgetSummary, useBudgets } from '@/hooks/useApi';
import { formatCurrency, formatTokens, getAgentColor } from '@/lib/utils';

// Mock data
const dailySpending = [
  { date: 'Jan 12', cost: 3.45, tokens: 125000 },
  { date: 'Jan 13', cost: 4.12, tokens: 148000 },
  { date: 'Jan 14', cost: 2.89, tokens: 102000 },
  { date: 'Jan 15', cost: 5.23, tokens: 189000 },
  { date: 'Jan 16', cost: 3.78, tokens: 136000 },
  { date: 'Jan 17', cost: 4.56, tokens: 165000 },
  { date: 'Jan 18', cost: 2.34, tokens: 85000 },
];

const agentCosts = [
  { name: 'Builder', cost: 18.50, color: getAgentColor('builder') },
  { name: 'Planner', cost: 8.20, color: getAgentColor('planner') },
  { name: 'Reviewer', cost: 12.30, color: getAgentColor('reviewer') },
  { name: 'Tester', cost: 5.80, color: getAgentColor('tester') },
  { name: 'Documenter', cost: 3.20, color: getAgentColor('documenter') },
];

const budgetAlerts = [
  { agent: 'Builder', usage: 46, limit: 40, message: 'Approaching 50% of monthly limit' },
  { agent: 'Reviewer', usage: 49, limit: 25, message: 'Nearing 50% threshold' },
];

export function BudgetPage() {
  // Fetch data (will be used when backend is ready)
  useBudgetSummary();
  useBudgets();

  const totalBudget = 100;
  const totalUsed = agentCosts.reduce((sum, a) => sum + a.cost, 0);
  const percentUsed = (totalUsed / totalBudget) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Budget</h1>
          <p className="text-muted-foreground">Track spending and manage cost limits</p>
        </div>
        <Button>
          <Settings className="mr-2 h-4 w-4" />
          Configure Limits
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Budget</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBudget)}</div>
            <Progress value={percentUsed} className="mt-2 h-2" />
            <p className="mt-1 text-xs text-muted-foreground">
              {formatCurrency(totalUsed)} used ({percentUsed.toFixed(1)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Spend</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(2.34)}</div>
            <p className="text-xs text-muted-foreground">
              {formatTokens(85000)} tokens
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <TrendingDown className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(26.37)}</div>
            <p className="text-xs text-green-600">8% under last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Remaining</CardTitle>
            <Wallet className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBudget - totalUsed)}</div>
            <p className="text-xs text-muted-foreground">Until Jan 31</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {budgetAlerts.length > 0 && (
        <Card className="border-yellow-500/50 bg-yellow-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-600">
              <AlertTriangle className="h-5 w-5" />
              Budget Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {budgetAlerts.map((alert, idx) => (
                <div key={idx} className="flex items-center justify-between rounded-lg bg-background p-3">
                  <div>
                    <span className="font-medium">{alert.agent}</span>
                    <span className="text-muted-foreground"> - {alert.message}</span>
                  </div>
                  <span className="text-sm font-medium text-yellow-600">{alert.usage}% used</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Spending Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Spending</CardTitle>
            <CardDescription>Cost trend over the past week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dailySpending}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" className="text-xs" />
                  <YAxis className="text-xs" tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      name === 'cost' ? formatCurrency(value) : formatTokens(value),
                      name === 'cost' ? 'Cost' : 'Tokens',
                    ]}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={{ fill: 'hsl(var(--primary))' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Cost by Agent */}
        <Card>
          <CardHeader>
            <CardTitle>Cost by Agent</CardTitle>
            <CardDescription>Monthly spending distribution</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={agentCosts}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="cost"
                  >
                    {agentCosts.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => [formatCurrency(value), 'Cost']}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="mt-4 flex flex-wrap justify-center gap-4">
              {agentCosts.map((agent) => (
                <div key={agent.name} className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: agent.color }} />
                  <span className="text-sm">{agent.name}</span>
                  <span className="text-sm text-muted-foreground">{formatCurrency(agent.cost)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Per-Agent Budgets */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Agent Budgets</CardTitle>
              <CardDescription>Individual limits per agent role</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Add Limit
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { agent: 'Builder', limit: 40, used: 18.50 },
              { agent: 'Reviewer', limit: 25, used: 12.30 },
              { agent: 'Planner', limit: 20, used: 8.20 },
              { agent: 'Tester', limit: 15, used: 5.80 },
              { agent: 'Documenter', limit: 10, used: 3.20 },
            ].map((item) => (
              <div key={item.agent} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: getAgentColor(item.agent.toLowerCase()) }}
                    />
                    <span className="font-medium">{item.agent}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">{formatCurrency(item.used)}</span>
                    <span className="text-muted-foreground"> / {formatCurrency(item.limit)}</span>
                  </div>
                </div>
                <Progress value={(item.used / item.limit) * 100} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
