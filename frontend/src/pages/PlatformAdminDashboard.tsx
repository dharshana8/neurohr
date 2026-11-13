import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LogOut, Building2, Plus, Copy, Check, Users, Search, 
  RefreshCw, Key, Shield, Eye, EyeOff, AlertCircle,
  Activity, Sparkles, Zap, Lock, CheckCircle2,
  TrendingUp, Layers, Server, Briefcase, MessageSquare,
  LogIn, Trash2, Sliders, ToggleLeft, ToggleRight, DollarSign, Database, Cpu, ShieldCheck
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Organization {
  id: string;
  name: string;
  industry: string | null;
  company_size: string | null;
  status: string;
  plan_tier?: string;
  subscription_status?: string;
  plan_limits?: {
    max_employees: number;
    features: string[];
    max_integrations: number;
    copilot_access: boolean;
    description: string;
  };
  admin_email: string | null;
  employee_count: number;
  created_at: string | null;
}

interface TelemetryData {
  organization_id: string;
  organization_name: string;
  plan_tier: string;
  subscription_status: string;
  plan_limits: {
    max_employees: number;
    features: string[];
    max_integrations: number;
    copilot_access: boolean;
    description: string;
  };
  seat_capacity: {
    current_employees: number;
    max_employees: number;
    utilization_pct: number;
  };
  activity_metrics: {
    attrition_predictions_count: number;
    jobs_posted_count: number;
    candidates_tracked_count: number;
    sentiment_surveys_logged: number;
    integrations_connected: number;
    audit_events_logged: number;
  };
  last_activity: string | null;
  privacy_notice: string;
}

interface AuditLogItem {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  status: string;
  timestamp: string;
}

interface CreatedCustomerCredentials {
  organization_name: string;
  organization_id: string;
  plan_tier: string;
  admin_email: string;
  admin_password: string;
}

interface SystemHealthData {
  status: string;
  uptime_pct: number;
  api_latency_ms: number;
  db_cluster: {
    status: string;
    type: string;
    active_connections: number;
    read_latency_ms: number;
  };
  ml_inference_cluster: {
    engine: string;
    status: string;
    avg_prediction_latency_ms: number;
  };
  metrics: {
    total_tenants: number;
    active_tenants: number;
    total_cross_tenant_workforce: number;
    monthly_recurring_revenue_inr: number;
    ai_tokens_consumed_month: number;
    total_audit_events: number;
  };
  platform_settings: {
    maintenance_mode: boolean;
    global_copilot_enabled: boolean;
    mfa_enforced: boolean;
    allow_self_registration: boolean;
    max_tenants_limit: number;
  };
}

export default function PlatformAdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'organizations' | 'audit_logs' | 'governance'>('organizations');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealthData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'SUSPENDED'>('ALL');
  const [tierFilter, setTierFilter] = useState<'ALL' | 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE'>('ALL');

  // Register Organization Modal State
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [orgName, setOrgName] = useState('');
  const [industry, setIndustry] = useState('Technology & AI');
  const [companySize, setCompanySize] = useState('51-200');
  const [selectedPlanTier, setSelectedPlanTier] = useState<'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE'>('PROFESSIONAL');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Success Modal for Customer Credentials
  const [credentialsModal, setCredentialsModal] = useState<CreatedCustomerCredentials | null>(null);
  const [copied, setCopied] = useState(false);

  // Reset Admin Modal State
  const [resetAdminModal, setResetAdminModal] = useState<{ orgId: string; orgName: string; currentEmail: string } | null>(null);
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [newAdminPassword, setNewAdminPassword] = useState('');
  const [resetSuccessCredentials, setResetSuccessCredentials] = useState<{ email: string; password: string; orgName: string } | null>(null);

  // Telemetry Modal State
  const [telemetryOrg, setTelemetryOrg] = useState<Organization | null>(null);
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [isLoadingTelemetry, setIsLoadingTelemetry] = useState(false);
  const [isUpdatingPlan, setIsUpdatingPlan] = useState(false);
  const [planChangeMsg, setPlanChangeMsg] = useState('');

  // Feature Flags State
  const [featureFlags, setFeatureFlags] = useState({
    maintenance_mode: false,
    global_copilot_enabled: true,
    mfa_enforced: false,
    allow_self_registration: false
  });
  const [isUpdatingFlag, setIsUpdatingFlag] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchOrgs = async () => {
    try {
      setIsLoading(true);
      const res = await axios.get('http://localhost:8000/api/v1/platform-admin/organizations', {
        headers: getAuthHeaders()
      });
      setOrganizations(res.data);
    } catch (error) {
      console.error('Error fetching organizations', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/platform-admin/audit-logs', {
        headers: getAuthHeaders()
      });
      setAuditLogs(res.data);
    } catch (error) {
      console.error('Error fetching audit logs', error);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/platform-admin/system-health', {
        headers: getAuthHeaders()
      });
      setSystemHealth(res.data);
      if (res.data.platform_settings) {
        setFeatureFlags({
          maintenance_mode: res.data.platform_settings.maintenance_mode,
          global_copilot_enabled: res.data.platform_settings.global_copilot_enabled,
          mfa_enforced: res.data.platform_settings.mfa_enforced,
          allow_self_registration: res.data.platform_settings.allow_self_registration
        });
      }
    } catch (err) {
      console.error('Error fetching system health', err);
    }
  };

  useEffect(() => {
    fetchOrgs();
    fetchAuditLogs();
    fetchSystemHealth();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*';
    let pwd = '';
    for (let i = 0; i < 12; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return pwd;
  };

  const openRegisterModal = () => {
    setOrgName('');
    setIndustry('Technology & AI');
    setCompanySize('51-200');
    setSelectedPlanTier('PROFESSIONAL');
    setAdminEmail('');
    setAdminPassword(generateRandomPassword());
    setFormError('');
    setIsRegisterModalOpen(true);
  };

  const handleRegisterTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!orgName.trim() || !adminEmail.trim() || !adminPassword.trim()) {
      setFormError('Please fill in all required fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await axios.post('http://localhost:8000/api/v1/platform-admin/register-tenant', {
        organization_name: orgName.trim(),
        industry,
        company_size: companySize,
        plan_tier: selectedPlanTier,
        admin_email: adminEmail.trim(),
        admin_password: adminPassword
      }, {
        headers: getAuthHeaders()
      });

      setIsRegisterModalOpen(false);
      setCredentialsModal({
        organization_name: res.data.organization_name,
        organization_id: res.data.organization_id,
        plan_tier: res.data.plan_tier || selectedPlanTier,
        admin_email: res.data.admin_email,
        admin_password: res.data.admin_password
      });

      await fetchOrgs();
      await fetchAuditLogs();
      await fetchSystemHealth();
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to register organization');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (org: Organization) => {
    const newStatus = org.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
    const confirmMsg = `Are you sure you want to ${newStatus === 'SUSPENDED' ? 'SUSPEND' : 'ACTIVATE'} organization "${org.name}"?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await axios.put(`http://localhost:8000/api/v1/platform-admin/organizations/${org.id}/status?status=${newStatus}`, {}, {
        headers: getAuthHeaders()
      });
      await fetchOrgs();
      await fetchAuditLogs();
      await fetchSystemHealth();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleImpersonateTenant = async (org: Organization) => {
    const confirmMsg = `Diagnostic Impersonation Mode:\n\nDo you want to log in as Organization Admin for "${org.name}" to audit and troubleshoot their dashboard?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      const res = await axios.post(`http://localhost:8000/api/v1/platform-admin/organizations/${org.id}/impersonate`, {}, {
        headers: getAuthHeaders()
      });
      
      const currentToken = localStorage.getItem('token');
      localStorage.setItem('superadmin_backup_token', currentToken || '');
      localStorage.setItem('token', res.data.impersonation_token);
      
      alert(`Diagnostic session active for "${org.name}". Launching organization workspace...`);
      window.location.href = '/dashboard/overview';
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to initiate tenant impersonation');
    }
  };

  const handleDeleteTenant = async (org: Organization) => {
    if (org.id === 'org_acme_corp') {
      alert('Default demo tenant "Acme Corporation" is locked and cannot be deleted.');
      return;
    }

    const confirmMsg = `CRITICAL ACTION:\n\nAre you sure you want to DECOMMISSION and DELETE "${org.name}" (${org.id})?\n\nThis will remove all tenant mappings from the platform.`;
    if (!window.confirm(confirmMsg)) return;

    try {
      await axios.delete(`http://localhost:8000/api/v1/platform-admin/organizations/${org.id}`, {
        headers: getAuthHeaders()
      });
      alert(`Tenant "${org.name}" successfully decommissioned.`);
      await fetchOrgs();
      await fetchAuditLogs();
      await fetchSystemHealth();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete tenant');
    }
  };

  const handleOpenResetAdmin = (org: Organization) => {
    setResetAdminModal({
      orgId: org.id,
      orgName: org.name,
      currentEmail: org.admin_email || ''
    });
    setNewAdminEmail(org.admin_email || `admin@${org.name.toLowerCase().replace(/[^a-z0-9]/g, '')}.com`);
    setNewAdminPassword(generateRandomPassword());
  };

  const handleSaveAdminCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetAdminModal) return;

    try {
      setIsSubmitting(true);
      await axios.post(`http://localhost:8000/api/v1/platform-admin/organizations/${resetAdminModal.orgId}/admin`, {
        email: newAdminEmail.trim(),
        password: newAdminPassword
      }, {
        headers: getAuthHeaders()
      });

      setResetSuccessCredentials({
        email: newAdminEmail.trim(),
        password: newAdminPassword,
        orgName: resetAdminModal.orgName
      });
      setResetAdminModal(null);
      await fetchOrgs();
      await fetchAuditLogs();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to provision admin credentials');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenTelemetry = async (org: Organization) => {
    setTelemetryOrg(org);
    setTelemetryData(null);
    setPlanChangeMsg('');
    setIsLoadingTelemetry(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/platform-admin/organizations/${org.id}/telemetry`, {
        headers: getAuthHeaders()
      });
      setTelemetryData(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to fetch customer telemetry');
      setTelemetryOrg(null);
    } finally {
      setIsLoadingTelemetry(false);
    }
  };

  const handleUpdatePlanTier = async (newTier: string) => {
    if (!telemetryOrg) return;
    try {
      setIsUpdatingPlan(true);
      setPlanChangeMsg('');
      await axios.put(`http://localhost:8000/api/v1/platform-admin/organizations/${telemetryOrg.id}/plan`, {
        plan_tier: newTier
      }, {
        headers: getAuthHeaders()
      });
      setPlanChangeMsg(`Plan successfully updated to ${newTier}!`);
      const res = await axios.get(`http://localhost:8000/api/v1/platform-admin/organizations/${telemetryOrg.id}/telemetry`, {
        headers: getAuthHeaders()
      });
      setTelemetryData(res.data);
      await fetchOrgs();
      await fetchAuditLogs();
      await fetchSystemHealth();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update plan tier');
    } finally {
      setIsUpdatingPlan(false);
    }
  };

  const handleToggleFeatureFlag = async (key: string, currentVal: boolean) => {
    try {
      setIsUpdatingFlag(true);
      const payload = { [key]: !currentVal };
      const res = await axios.put('http://localhost:8000/api/v1/platform-admin/feature-flags', payload, {
        headers: getAuthHeaders()
      });
      setFeatureFlags(res.data.settings);
      await fetchAuditLogs();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update feature flag');
    } finally {
      setIsUpdatingFlag(false);
    }
  };

  const copyCustomerText = (orgName: string, email: string, pass: string, planTier: string = 'STARTER') => {
    const text = `======================================
Welcome to NeuroHR X Platform!
======================================
Organization:      ${orgName}
Subscription Plan: ${planTier}
Platform Login:    http://localhost:5173/login

Administrator Credentials:
Email:    ${email}
Password: ${pass}

* Please change your password upon your first sign in.
======================================`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const getPlanBadge = (tier: string = 'STARTER') => {
    switch (tier.toUpperCase()) {
      case 'ENTERPRISE':
        return {
          label: 'Enterprise',
          badgeClass: 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-extrabold shadow-sm',
          price: '₹2,50,000 / mo',
          icon: <Sparkles className="h-3 w-3" />
        };
      case 'PROFESSIONAL':
        return {
          label: 'Professional',
          badgeClass: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 font-bold',
          price: '₹85,000 / mo',
          icon: <Zap className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
        };
      default:
        return {
          label: 'Starter',
          badgeClass: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 font-semibold',
          price: '₹25,000 / mo',
          icon: <Layers className="h-3 w-3 text-gray-500" />
        };
    }
  };

  const activeCount = organizations.filter(o => o.status === 'ACTIVE').length;
  const suspendedCount = organizations.filter(o => o.status === 'SUSPENDED').length;
  const totalEmployees = organizations.reduce((acc, o) => acc + (o.employee_count || 0), 0);
  const mrrInr = systemHealth?.metrics?.monthly_recurring_revenue_inr || 610000;

  const filteredOrgs = organizations.filter(org => {
    const matchesSearch = 
      org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (org.admin_email && org.admin_email.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (org.industry && org.industry.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = statusFilter === 'ALL' || org.status === statusFilter;
    const matchesTier = tierFilter === 'ALL' || (org.plan_tier || 'STARTER').toUpperCase() === tierFilter;
    return matchesSearch && matchesStatus && matchesTier;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 font-sans text-gray-900 dark:text-gray-100">
      {/* Top Navigation Bar */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-30 shadow-sm">
        <div className="flex h-16 items-center justify-between px-6 max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 text-white font-black shadow-md shadow-indigo-500/20">
              NX
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight">
                NeuroHR <span className="text-indigo-600 dark:text-indigo-400">Platform Command Center</span>
              </span>
              <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                SuperAdmin Root
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-semibold">{user?.email || 'admin@neurohr.com'}</p>
              <p className="text-xs text-indigo-600 dark:text-indigo-400 font-mono font-medium">SUPERADMIN_ROOT</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 transition"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Banner with Primary Call to Action */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-purple-950 text-white p-6 sm:p-8 rounded-2xl shadow-xl relative overflow-hidden border border-indigo-800/40">
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/30 text-indigo-200 tracking-wide uppercase backdrop-blur-sm border border-indigo-400/30">
                Multi-Tenant Governance & Revenue Hub
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Platform SuperAdmin Control Center</h1>
            <p className="text-indigo-200 text-sm sm:text-base mt-1 max-w-2xl">
              Full administrative authority to provision customer organizations, manage subscriptions in Indian Rupees (₹), rotate tenant credentials, impersonate tenant sessions for troubleshooting, and govern global system telemetry.
            </p>
          </div>
          <div className="relative z-10 flex flex-wrap gap-3">
            <button
              onClick={openRegisterModal}
              className="flex items-center gap-2 px-5 py-3 bg-indigo-500 hover:bg-indigo-400 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/30 active:scale-95 transition-all text-sm"
            >
              <Plus className="h-5 w-5 font-bold" />
              <span>Onboard New Organization</span>
            </button>
          </div>
          {/* Background decorative glow */}
          <div className="absolute right-0 top-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        </div>

        {/* Global Live System SLA & Infrastructure Bar */}
        <div className="bg-slate-900 text-white p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-sm text-xs">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="font-bold">System SLA:</span>
              <span className="text-emerald-400 font-mono font-bold">99.98% Operational</span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-indigo-400" />
              <span>API Latency:</span>
              <span className="font-mono text-indigo-300 font-bold">{systemHealth?.api_latency_ms || 32}ms</span>
            </div>
            <div className="hidden md:flex items-center gap-2">
              <Database className="h-3.5 w-3.5 text-blue-400" />
              <span>MongoDB ReplicaSet:</span>
              <span className="text-blue-300 font-bold">Healthy (14 conns)</span>
            </div>
            <div className="hidden lg:flex items-center gap-2">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              <span>ML Random Forest:</span>
              <span className="text-purple-300 font-bold">Optimal (11ms)</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700 font-mono">
              <span className="text-gray-400">Monthly Recurring Revenue:</span>{' '}
              <span className="text-emerald-400 font-bold">₹{mrrInr.toLocaleString('en-IN')}/mo</span>
            </div>
          </div>
        </div>

        {/* Top Metric Cards */}
        <div className="grid gap-5 grid-cols-1 sm:grid-cols-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Organizations</span>
              <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600">
                <Building2 className="h-5 w-5" />
              </div>
            </div>
            <div className="text-3xl font-black mt-2">{isLoading ? '...' : organizations.length}</div>
            <div className="mt-3 flex items-center gap-3 text-xs">
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> {activeCount} Active
              </span>
              <span className="inline-flex items-center gap-1 font-semibold text-red-500">
                <span className="w-2 h-2 rounded-full bg-red-500"></span> {suspendedCount} Suspended
              </span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Enterprise Tenants</span>
              <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-500/10 text-purple-600">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>
            <div className="text-3xl font-black mt-2">
              {isLoading ? '...' : organizations.filter(o => (o.plan_tier || '').toUpperCase() === 'ENTERPRISE').length}
            </div>
            <p className="text-xs text-gray-500 mt-3">Full Gemini 2.0 AI & RAG Copilot tier</p>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Workforce</span>
              <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600">
                <Users className="h-5 w-5" />
              </div>
            </div>
            <div className="text-3xl font-black mt-2">{isLoading ? '...' : totalEmployees}</div>
            <p className="text-xs text-gray-500 mt-3">Active employees across all tenants</p>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Platform MRR (INR)</span>
              <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-2 font-mono">
              ₹{(mrrInr / 100000).toFixed(2)} Lakhs
            </div>
            <p className="text-xs text-gray-500 mt-2">Total recurring revenue per month</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('organizations')}
              className={`pb-3 px-4 font-bold text-sm border-b-2 transition-colors ${
                activeTab === 'organizations'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              Organizations & Tenants ({organizations.length})
            </button>
            <button
              onClick={() => setActiveTab('audit_logs')}
              className={`pb-3 px-4 font-bold text-sm border-b-2 transition-colors ${
                activeTab === 'audit_logs'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              Platform Audit Logs ({auditLogs.length})
            </button>
            <button
              onClick={() => setActiveTab('governance')}
              className={`pb-3 px-4 font-bold text-sm border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'governance'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              <Sliders className="h-3.5 w-3.5" />
              <span>Platform Governance & Controls</span>
            </button>
          </div>
          <button
            onClick={() => { fetchOrgs(); fetchAuditLogs(); fetchSystemHealth(); }}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 pb-2 transition"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* TAB 1: Organizations View */}
        {activeTab === 'organizations' && (
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
            {/* Search and Filters */}
            <div className="p-4 sm:p-5 border-b border-gray-200 dark:border-gray-800 flex flex-col md:flex-row gap-3 items-center justify-between bg-gray-50/50 dark:bg-gray-900/50">
              <div className="relative w-full md:w-72">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, admin email, industry..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="px-3 py-2 text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-medium"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">Active Only</option>
                  <option value="SUSPENDED">Suspended Only</option>
                </select>

                <select
                  value={tierFilter}
                  onChange={(e) => setTierFilter(e.target.value as any)}
                  className="px-3 py-2 text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-medium"
                >
                  <option value="ALL">All Subscription Tiers</option>
                  <option value="STARTER">Starter Tier</option>
                  <option value="PROFESSIONAL">Professional Tier</option>
                  <option value="ENTERPRISE">Enterprise Tier</option>
                </select>
              </div>
            </div>

            {/* Organizations Cards List */}
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {isLoading ? (
                <div className="p-12 text-center text-gray-500">
                  <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
                  Loading customer tenant organizations...
                </div>
              ) : filteredOrgs.length === 0 ? (
                <div className="p-12 text-center text-gray-500">
                  <Building2 className="h-10 w-10 mx-auto mb-2 text-gray-400" />
                  <p className="font-semibold">No customer organizations found</p>
                  <p className="text-xs text-gray-400 mt-1">Try changing your search terms or filters</p>
                </div>
              ) : (
                filteredOrgs.map((org) => {
                  const plan = getPlanBadge(org.plan_tier);
                  return (
                    <div
                      key={org.id}
                      className="p-5 sm:p-6 hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      {/* Left: Org Info */}
                      <div className="space-y-1.5 max-w-xl">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            {org.name}
                          </h3>

                          {/* Plan Badge */}
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] ${plan.badgeClass}`}>
                            {plan.icon}
                            {plan.label}
                          </span>

                          {/* Status Badge */}
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                            org.status === 'ACTIVE'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                          }`}>
                            {org.status}
                          </span>

                          <span className="text-xs text-emerald-600 font-mono font-bold">
                            {plan.price}
                          </span>
                        </div>

                        <p className="text-xs text-gray-500 dark:text-gray-400 flex flex-wrap items-center gap-x-3 gap-y-1">
                          <span>{org.industry || 'General Industry'}</span>
                          <span>•</span>
                          <span>Customer Admin: <strong className="text-gray-700 dark:text-gray-300 font-mono">{org.admin_email || 'Not configured'}</strong></span>
                          <span>•</span>
                          <span>Employees: <strong>{org.employee_count}</strong></span>
                          <span>•</span>
                          <span>Company Size: {org.company_size || 'N/A'}</span>
                          <span>•</span>
                          <span className="font-mono text-[11px] text-gray-400">ID: {org.id}</span>
                        </p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-wrap items-center gap-2 self-start md:self-center">
                        {/* Impersonate / Login as Tenant Button */}
                        <button
                          onClick={() => handleImpersonateTenant(org)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-blue-50 hover:bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 dark:text-blue-300 rounded-lg border border-blue-200 dark:border-blue-800 transition shadow-sm"
                          title="Log in directly as Tenant Admin to diagnose issues in customer workspace"
                        >
                          <LogIn className="h-3.5 w-3.5 text-blue-600" />
                          <span>Login as Tenant</span>
                        </button>

                        {/* Telemetry & Performance Button */}
                        <button
                          onClick={() => handleOpenTelemetry(org)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-purple-50 hover:bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:hover:bg-purple-900/50 dark:text-purple-300 rounded-lg border border-purple-200 dark:border-purple-800 transition"
                          title="View customer performance, feature usage, and plan quotas"
                        >
                          <Activity className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
                          <span>Performance & Telemetry</span>
                        </button>

                        <button
                          onClick={() => handleOpenResetAdmin(org)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:hover:bg-indigo-900/50 dark:text-indigo-300 rounded-lg border border-indigo-200 dark:border-indigo-800 transition"
                          title="Provision new or updated credentials for this tenant"
                        >
                          <Key className="h-3.5 w-3.5" />
                          <span>Reset/Issue Admin</span>
                        </button>

                        <button
                          onClick={() => handleToggleStatus(org)}
                          className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
                            org.status === 'ACTIVE'
                              ? 'text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/30 border-amber-200 dark:border-amber-900'
                              : 'text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900'
                          }`}
                        >
                          {org.status === 'ACTIVE' ? 'Suspend Tenant' : 'Activate Tenant'}
                        </button>

                        {/* Decommission Tenant Button */}
                        {org.id !== 'org_acme_corp' && (
                          <button
                            onClick={() => handleDeleteTenant(org)}
                            className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg border border-transparent hover:border-red-200 transition"
                            title="Decommission & Delete Tenant"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* TAB 2: Platform Audit Logs View */}
        {activeTab === 'audit_logs' && (
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
              <h3 className="font-bold text-sm text-gray-900 dark:text-white">Global Platform Audit Trail</h3>
              <span className="text-xs text-gray-500 font-mono">Real-time immutable logging</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 dark:bg-gray-800/60 text-gray-500 uppercase tracking-wider">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Resource Type</th>
                    <th className="p-3">Resource ID</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-800 font-mono">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-gray-500">No platform audit logs recorded yet.</td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/40">
                        <td className="p-3 text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                        <td className="p-3 font-bold text-gray-900 dark:text-gray-100">{log.action}</td>
                        <td className="p-3 text-gray-600 dark:text-gray-300">{log.resource_type}</td>
                        <td className="p-3 text-gray-400">{log.resource_id || '—'}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: Platform Governance & Feature Controls */}
        {activeTab === 'governance' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
              <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Sliders className="h-5 w-5 text-indigo-600" />
                Global Platform Governance & Kill-Switches
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Configure platform-wide security policies, emergency kill-switches, and automated onboarding restrictions.
              </p>

              <div className="mt-6 divide-y divide-gray-200 dark:divide-gray-800">
                {/* Maintenance Mode */}
                <div className="py-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-gray-900 dark:text-white">Emergency Maintenance Mode</h4>
                    <p className="text-xs text-gray-500">Locks tenant user logins and displays scheduled maintenance notice across all portals.</p>
                  </div>
                  <button
                    disabled={isUpdatingFlag}
                    onClick={() => handleToggleFeatureFlag('maintenance_mode', featureFlags.maintenance_mode)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition ${
                      featureFlags.maintenance_mode 
                        ? 'bg-red-600 text-white' 
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {featureFlags.maintenance_mode ? <ToggleRight className="h-5 w-5 text-white" /> : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                    <span>{featureFlags.maintenance_mode ? 'ENABLED (LOCKED)' : 'DISABLED'}</span>
                  </button>
                </div>

                {/* Global AI Copilot */}
                <div className="py-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-gray-900 dark:text-white">Global AI & Copilot Engine</h4>
                    <p className="text-xs text-gray-500">Allows customer organizations with Professional/Enterprise licenses to execute Google Gemini 2.0 AI queries.</p>
                  </div>
                  <button
                    disabled={isUpdatingFlag}
                    onClick={() => handleToggleFeatureFlag('global_copilot_enabled', featureFlags.global_copilot_enabled)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition ${
                      featureFlags.global_copilot_enabled 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {featureFlags.global_copilot_enabled ? <ToggleRight className="h-5 w-5 text-white" /> : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                    <span>{featureFlags.global_copilot_enabled ? 'ONLINE & ACTIVE' : 'PAUSED'}</span>
                  </button>
                </div>

                {/* MFA Enforced */}
                <div className="py-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-gray-900 dark:text-white">Mandatory Multi-Factor Authentication (MFA)</h4>
                    <p className="text-xs text-gray-500">Enforces two-factor cryptographic challenge for all customer Organization Admins.</p>
                  </div>
                  <button
                    disabled={isUpdatingFlag}
                    onClick={() => handleToggleFeatureFlag('mfa_enforced', featureFlags.mfa_enforced)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition ${
                      featureFlags.mfa_enforced 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {featureFlags.mfa_enforced ? <ToggleRight className="h-5 w-5 text-white" /> : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                    <span>{featureFlags.mfa_enforced ? 'ENFORCED' : 'OPTIONAL'}</span>
                  </button>
                </div>

                {/* Self Registration */}
                <div className="py-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-gray-900 dark:text-white">Public Self-Registration Gateway</h4>
                    <p className="text-xs text-gray-500">Allows public companies to register Starter tier trials directly from platform home page.</p>
                  </div>
                  <button
                    disabled={isUpdatingFlag}
                    onClick={() => handleToggleFeatureFlag('allow_self_registration', featureFlags.allow_self_registration)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs transition ${
                      featureFlags.allow_self_registration 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {featureFlags.allow_self_registration ? <ToggleRight className="h-5 w-5 text-white" /> : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                    <span>{featureFlags.allow_self_registration ? 'OPEN FOR SIGNUP' : 'INVITE/ADMIN ONLY'}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ========================================================================= */}
      {/* MODAL 1: Register New Organization & Customer Admin with Plan Selection */}
      {/* ========================================================================= */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            <div>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-indigo-600" />
                  Onboard Customer Organization
                </h2>
                <button
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm font-bold"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Provisions a dedicated multi-tenant boundary, binds a subscription plan with Indian Rupee (₹) billing, and configures administrator credentials.
              </p>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-xs text-red-700 dark:text-red-300">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleRegisterTenant} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Organization Legal Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation or Bharat Tech Labs"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-gray-600 dark:text-gray-400 mb-1">
                    Industry Domain
                  </label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm"
                  >
                    <option value="Technology & AI">Technology & AI</option>
                    <option value="FinTech & Banking">FinTech & Banking</option>
                    <option value="Logistics & Supply Chain">Logistics & Supply Chain</option>
                    <option value="Healthcare & Life Sciences">Healthcare & Life Sciences</option>
                    <option value="Automotive & Robotics">Automotive & Robotics</option>
                    <option value="E-Commerce & Retail">E-Commerce & Retail</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-gray-600 dark:text-gray-400 mb-1">
                    Workforce Company Size
                  </label>
                  <select
                    value={companySize}
                    onChange={(e) => setCompanySize(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm"
                  >
                    <option value="1-10">1-10 Employees</option>
                    <option value="11-50">11-50 Employees</option>
                    <option value="51-200">51-200 Employees</option>
                    <option value="201-1000">201-1000 Employees</option>
                    <option value="1000+">1000+ Global Enterprise</option>
                  </select>
                </div>
              </div>

              {/* Plan Tier Selector */}
              <div>
                <label className="block font-bold text-gray-700 dark:text-gray-300 mb-2">
                  Select Subscription Tier (Billed in INR ₹) *
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {/* STARTER */}
                  <div
                    onClick={() => setSelectedPlanTier('STARTER')}
                    className={`cursor-pointer p-3 rounded-xl border transition-all ${
                      selectedPlanTier === 'STARTER'
                        ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 ring-2 ring-indigo-500/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-gray-900 dark:text-white">Starter</span>
                      {selectedPlanTier === 'STARTER' && <CheckCircle2 className="h-4 w-4 text-indigo-600" />}
                    </div>
                    <p className="text-[12px] font-mono font-bold text-emerald-600">₹25,000 / mo</p>
                    <p className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 mt-1">Up to 50 seats</p>
                    <p className="text-[10px] text-gray-500 mt-1">Core workforce, CSV import, attrition risk engine.</p>
                  </div>

                  {/* PROFESSIONAL */}
                  <div
                    onClick={() => setSelectedPlanTier('PROFESSIONAL')}
                    className={`cursor-pointer p-3 rounded-xl border transition-all ${
                      selectedPlanTier === 'PROFESSIONAL'
                        ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 ring-2 ring-indigo-500/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-gray-900 dark:text-white">Professional</span>
                      {selectedPlanTier === 'PROFESSIONAL' && <CheckCircle2 className="h-4 w-4 text-indigo-600" />}
                    </div>
                    <p className="text-[12px] font-mono font-bold text-emerald-600">₹85,000 / mo</p>
                    <p className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 mt-1">Up to 300 seats</p>
                    <p className="text-[10px] text-gray-500 mt-1">ERP sync, HRIS leave AI, sentiment & Copilot.</p>
                  </div>

                  {/* ENTERPRISE */}
                  <div
                    onClick={() => setSelectedPlanTier('ENTERPRISE')}
                    className={`cursor-pointer p-3 rounded-xl border transition-all ${
                      selectedPlanTier === 'ENTERPRISE'
                        ? 'border-purple-600 bg-purple-50/50 dark:bg-purple-950/30 ring-2 ring-purple-500/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-sm text-purple-700 dark:text-purple-300 flex items-center gap-1">
                        <Sparkles className="h-3.5 w-3.5" /> Enterprise
                      </span>
                      {selectedPlanTier === 'ENTERPRISE' && <CheckCircle2 className="h-4 w-4 text-purple-600" />}
                    </div>
                    <p className="text-[12px] font-mono font-bold text-emerald-600">₹2,50,000 / mo</p>
                    <p className="text-[11px] font-bold text-purple-600 dark:text-purple-400 mt-1">Up to 5,000 seats</p>
                    <p className="text-[10px] text-gray-500 mt-1">Unlimited integrations, custom ML, dedicated SLA.</p>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-800 pt-4">
                <h3 className="font-bold text-gray-900 dark:text-gray-100 text-sm mb-2 flex items-center gap-1.5">
                  <Key className="h-4 w-4 text-indigo-600" />
                  Initial Customer Administrator Credentials
                </h3>

                <div className="space-y-3">
                  <div>
                    <label className="block font-medium text-gray-600 dark:text-gray-400 mb-1">
                      Customer Admin Email *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. admin@acmecorp.com"
                      value={adminEmail}
                      onChange={(e) => setAdminEmail(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 text-sm"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="font-medium text-gray-600 dark:text-gray-400">
                        Initial Password *
                      </label>
                      <button
                        type="button"
                        onClick={() => setAdminPassword(generateRandomPassword())}
                        className="text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline font-semibold"
                      >
                        Generate Secure Password
                      </button>
                    </div>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={adminPassword}
                        onChange={(e) => setAdminPassword(e.target.value)}
                        className="w-full px-3 py-2 pr-10 font-mono text-sm bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition disabled:opacity-50 shadow-md shadow-indigo-500/20"
                >
                  {isSubmitting ? 'Provisioning Tenant...' : 'Onboard & Generate Credentials'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: Credentials Share Modal (Ready to Give to Customer) */}
      {/* ========================================================================= */}
      {credentialsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 border border-emerald-500/30 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="text-center">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-300 mb-2">
                <Check className="h-6 w-6 stroke-[3]" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Organization Provisioned Successfully!</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Copy and deliver the customer access credentials below to the organization administrator.
              </p>
            </div>

            {/* Formatted Customer Box */}
            <div className="p-4 bg-gray-50 dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2.5 font-mono text-xs">
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500 font-sans font-medium">Organization:</span>
                <span className="font-bold text-gray-900 dark:text-white">{credentialsModal.organization_name}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500 font-sans font-medium">Tenant ID:</span>
                <span className="text-gray-400">{credentialsModal.organization_id}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500 font-sans font-medium">Subscription Plan:</span>
                <span className="font-bold text-indigo-600 dark:text-indigo-400">{credentialsModal.plan_tier}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500 font-sans font-medium">Platform URL:</span>
                <span className="text-indigo-600 dark:text-indigo-400 font-bold">http://localhost:5173/login</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500 font-sans font-medium">Admin Email:</span>
                <span className="font-bold text-gray-900 dark:text-white">{credentialsModal.admin_email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 font-sans font-medium">Initial Password:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">{credentialsModal.admin_password}</span>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => copyCustomerText(
                  credentialsModal.organization_name,
                  credentialsModal.admin_email,
                  credentialsModal.admin_password,
                  credentialsModal.plan_tier
                )}
                className={`w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition shadow-md ${
                  copied 
                    ? 'bg-emerald-600 text-white' 
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white active:scale-98'
                }`}
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Copied Credentials to Clipboard!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    <span>Copy Customer Welcome Credentials</span>
                  </>
                )}
              </button>

              <button
                onClick={() => setCredentialsModal(null)}
                className="w-full py-2 text-xs font-semibold text-gray-500 hover:text-gray-800 dark:hover:text-gray-300 transition"
              >
                Done / Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: Performance & Privacy-Preserving Telemetry Modal */}
      {/* ========================================================================= */}
      {telemetryOrg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[92vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-gray-200 dark:border-gray-800 pb-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <Activity className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Tenant Performance & Telemetry
                  </h2>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Customer Organization: <strong className="text-gray-800 dark:text-gray-200">{telemetryOrg.name}</strong> • ID: <span className="font-mono text-gray-400">{telemetryOrg.id}</span>
                </p>
              </div>
              <button
                onClick={() => setTelemetryOrg(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* Privacy Shield Notice */}
            <div className="p-3.5 bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/80 rounded-xl flex items-start gap-2.5">
              <Lock className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed">
                <strong className="font-bold">Strict Tenant Data Privacy Protected:</strong> SuperAdmin monitors operational counts, feature usage, and plan capacity limits only. Raw employee records, salaries, candidate resumes, and private survey feedback texts are cryptographically segregated within the customer tenant.
              </div>
            </div>

            {isLoadingTelemetry ? (
              <div className="py-12 text-center text-gray-500">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
                Aggregating customer operational telemetry...
              </div>
            ) : telemetryData ? (
              <div className="space-y-5">
                {/* Plan Management Strip */}
                <div className="p-4 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-gray-500 font-medium">Assigned Tier:</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-base font-bold text-gray-900 dark:text-white">
                        {telemetryData.plan_tier} Tier
                      </span>
                      <span className="text-xs text-emerald-600 font-mono font-bold">
                        {getPlanBadge(telemetryData.plan_tier).price}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 font-medium">Change Plan:</span>
                    <div className="flex items-center gap-1.5">
                      {(['STARTER', 'PROFESSIONAL', 'ENTERPRISE'] as const).map((tier) => (
                        <button
                          key={tier}
                          disabled={isUpdatingPlan || telemetryData.plan_tier.toUpperCase() === tier}
                          onClick={() => handleUpdatePlanTier(tier)}
                          className={`px-2.5 py-1 text-[11px] font-bold rounded-lg border transition ${
                            telemetryData.plan_tier.toUpperCase() === tier
                              ? 'bg-indigo-600 text-white border-indigo-600 cursor-default'
                              : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                          }`}
                        >
                          {tier}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {planChangeMsg && (
                  <div className="p-3 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-lg text-xs text-emerald-700 dark:text-emerald-300 font-semibold flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>{planChangeMsg}</span>
                  </div>
                )}

                {/* Seat Capacity Bar */}
                <div className="p-4 bg-white dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-gray-700 dark:text-gray-300">Workforce Seat Capacity Utilization</span>
                    <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {telemetryData.seat_capacity.current_employees} / {telemetryData.seat_capacity.max_employees} Seats ({telemetryData.seat_capacity.utilization_pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all rounded-full ${
                        telemetryData.seat_capacity.utilization_pct > 90
                          ? 'bg-red-500'
                          : telemetryData.seat_capacity.utilization_pct > 70
                          ? 'bg-amber-500'
                          : 'bg-indigo-600'
                      }`}
                      style={{ width: `${Math.min(telemetryData.seat_capacity.utilization_pct, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Operational Activity Grid */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">
                    Aggregated Operational Metrics
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Predictions Executed</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.attrition_predictions_count}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Requisitions Posted</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.jobs_posted_count}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Candidates Screened</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.candidates_tracked_count}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Surveys Analyzed</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.sentiment_surveys_logged}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Connectors Active</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.integrations_connected}
                      </p>
                    </div>

                    <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-200 dark:border-gray-700">
                      <span className="text-[11px] text-gray-500 font-medium">Audit Events Recorded</span>
                      <p className="text-xl font-bold mt-1 text-gray-900 dark:text-white font-mono">
                        {telemetryData.activity_metrics.audit_events_logged}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-800">
              <button
                onClick={() => setTelemetryOrg(null)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 transition"
              >
                Close Telemetry View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 4: Reset & Issue Admin Credentials Modal */}
      {/* ========================================================================= */}
      {resetAdminModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Key className="h-5 w-5 text-indigo-600" />
                Issue Customer Admin Credentials
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Rotates or updates the customer administrator account for <strong>{resetAdminModal.orgName}</strong>.
              </p>
            </div>

            <form onSubmit={handleSaveAdminCredentials} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Customer Admin Email *
                </label>
                <input
                  type="email"
                  required
                  value={newAdminEmail}
                  onChange={(e) => setNewAdminEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="font-medium text-gray-600 dark:text-gray-400">
                    New Secure Password *
                  </label>
                  <button
                    type="button"
                    onClick={() => setNewAdminPassword(generateRandomPassword())}
                    className="text-[11px] text-indigo-600 hover:underline font-semibold"
                  >
                    Generate New
                  </button>
                </div>
                <input
                  type="text"
                  required
                  value={newAdminPassword}
                  onChange={(e) => setNewAdminPassword(e.target.value)}
                  className="w-full px-3 py-2 font-mono text-sm bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setResetAdminModal(null)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Updating...' : 'Update & Issue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 5: Reset Admin Success Modal */}
      {/* ========================================================================= */}
      {resetSuccessCredentials && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 border border-emerald-500/30 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 text-center">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-1">
              <Check className="h-6 w-6 stroke-[3]" />
            </div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Credentials Updated!</h2>
            <p className="text-xs text-gray-500">
              The administrator credentials for <strong>{resetSuccessCredentials.orgName}</strong> have been updated.
            </p>

            <div className="p-3 bg-gray-50 dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 font-mono text-xs text-left space-y-1">
              <p><span className="text-gray-500 font-sans">Email:</span> <strong>{resetSuccessCredentials.email}</strong></p>
              <p><span className="text-gray-500 font-sans">Password:</span> <strong className="text-emerald-600">{resetSuccessCredentials.password}</strong></p>
            </div>

            <button
              onClick={() => setResetSuccessCredentials(null)}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-md"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
