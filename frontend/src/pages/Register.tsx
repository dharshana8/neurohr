import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Building, ArrowRight, BrainCircuit, ShieldCheck, CheckCircle2, Users } from 'lucide-react';

export default function Register() {
  const [orgName, setOrgName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [companySize, setCompanySize] = useState('51-200');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setSubmitted(true);
    }, 800);
  };

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 selection:bg-indigo-500/30">
      {/* Left Panel - Branding & Visuals */}
      <div className="relative hidden w-1/2 lg:block overflow-hidden bg-indigo-900">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1573164713988-8665fc963095?q=80&w=2069&auto=format&fit=crop')] bg-cover bg-center opacity-20 mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-950/95 via-indigo-900/85 to-indigo-800/80"></div>
        
        <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-md shadow-inner">
              <BrainCircuit className="h-7 w-7 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">NeuroHR <span className="text-indigo-300">X</span></span>
          </div>

          <div className="max-w-xl space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/20 px-3.5 py-1 text-xs font-semibold tracking-wide text-indigo-200 backdrop-blur-md">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              EXCLUSIVE ENTERPRISE ACCESS
            </div>

            <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-white drop-shadow-md">
              Managed Enterprise <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 via-white to-purple-200">Onboarding</span>
            </h1>
            <p className="text-lg text-indigo-100/90 leading-relaxed max-w-lg font-medium">
              To guarantee strict multi-tenant data isolation and SLA performance, every client tenant is provisioned directly by NeuroHR administrators.
            </p>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm space-y-3">
              <div className="text-sm font-semibold text-white">How onboarding works:</div>
              <div className="flex items-start gap-3 text-xs text-indigo-100">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/30 text-[11px] font-bold text-white">1</span>
                <span>Submit your enterprise inquiry with workforce details.</span>
              </div>
              <div className="flex items-start gap-3 text-xs text-indigo-100">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/30 text-[11px] font-bold text-white">2</span>
                <span>NeuroHR platform team provisions your company tenant &amp; sandbox.</span>
              </div>
              <div className="flex items-start gap-3 text-xs text-indigo-100">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/30 text-[11px] font-bold text-white">3</span>
                <span>Your designated HR Lead receives activation credentials via secure invite.</span>
              </div>
            </div>
          </div>
          
          <div className="text-xs font-medium text-indigo-200/60 border-t border-indigo-800/60 pt-4">
            &copy; {new Date().getFullYear()} NeuroHR X. Enterprise Edition.
          </div>
        </div>
      </div>

      {/* Right Panel - Request Access Form */}
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-md space-y-8">
          
          {/* Mobile Header */}
          <div className="flex flex-col items-center justify-center lg:hidden mb-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 shadow-xl mb-4">
              <BrainCircuit className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">NeuroHR X</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1 font-medium text-center text-sm">Enterprise HR Intelligence</p>
          </div>

          {submitted ? (
            <div className="text-center space-y-6 py-6 animate-in fade-in">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Inquiry Received</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                  Thank you, <span className="font-semibold text-gray-900 dark:text-white">{fullName}</span>. Our NeuroHR platform team will review <span className="font-semibold text-gray-900 dark:text-white">{orgName}</span>'s workspace inquiry and reach out with your administrator login within 24 hours.
                </p>
              </div>
              <div className="pt-4">
                <button
                  onClick={() => navigate('/login')}
                  className="w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white hover:bg-indigo-700 shadow-lg shadow-indigo-600/20 transition-all"
                >
                  Return to Workspace Sign In
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 dark:bg-indigo-950/60 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Invitation Only &bull; Managed Onboarding
                </div>
                <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white lg:text-4xl">
                  Request Workspace
                </h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  To safeguard company data, tenant access is provisioned by NeuroHR administrators.
                </p>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="fullName">
                    Your Full Name
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    required
                    className="block w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                    placeholder="Jane Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="orgName">
                    Organization / Company Name
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Building className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      id="orgName"
                      type="text"
                      required
                      className="block w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                      placeholder="Acme Corporation"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="email">
                    Corporate Work Email
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Mail className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      id="email"
                      type="email"
                      required
                      className="block w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                      placeholder="jane.doe@acmecorp.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="companySize">
                    Workforce Size
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Users className="h-4 w-4 text-gray-400" />
                    </div>
                    <select
                      id="companySize"
                      className="block w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                      value={companySize}
                      onChange={(e) => setCompanySize(e.target.value)}
                    >
                      <option value="1-50">1 - 50 Employees</option>
                      <option value="51-200">51 - 200 Employees</option>
                      <option value="201-1000">201 - 1,000 Employees</option>
                      <option value="1000+">1,000+ Enterprise</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/25 focus:outline-none focus:ring-4 focus:ring-indigo-500/50 disabled:opacity-70 disabled:cursor-not-allowed mt-2"
                >
                  {isLoading ? 'Submitting Request...' : 'Request Tenant Workspace'}
                  {!isLoading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
                </button>
              </form>
              
              <div className="pt-4 border-t border-gray-100 dark:border-gray-800 text-center text-xs text-gray-500 dark:text-gray-400">
                Already have provisioned credentials?{' '}
                <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 transition-colors">
                  Sign in here &rarr;
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

