import React, { useState, useEffect } from 'react';
import {
  Cpu, Play, Layers, Activity, ShieldCheck, Zap,
  Server, RefreshCw, AlertTriangle, CheckCircle2,
  Terminal, BarChart3, Database, Sliders, Box, GitBranch, Atom
} from 'lucide-react';
import { ApiError, apiRequest, postJson } from './api';

const PRESETS: Record<string, string> = {
  "Bell State (EPR)": `qubit q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];`,

  "GHZ 4-Qubit Entanglement": `qubit q[4];
creg c[4];
h q[0];
cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];`,

  "Quantum Fourier Transform (QFT-3)": `qubit q[3];
creg c[3];
h q[0];
rz(1.570796) q[1];
cx q[0], q[1];
rz(-1.570796) q[1];
cx q[0], q[1];
h q[1];
swap q[0], q[2];`,

  "Grover's Search (3-Qubit)": `qubit q[3];
creg c[3];
h q[0];
h q[1];
h q[2];
// Oracle for |101>
x q[1];
cx q[0], q[2];
cx q[1], q[2];
x q[1];
// Diffusion operator
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
cx q[0], q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];`
};

export default function App() {
  const [activeTab, setActiveTab] = useState<'studio' | 'visualizer' | 'noise' | 'cluster' | 'verify' | 'benchmarks' | 'protocols'>('studio');
  const [code, setCode] = useState<string>(PRESETS["Bell State (EPR)"]);
  const [backend, setBackend] = useState<string>('adaptive');
  const [optLevel, setOptLevel] = useState<number>(2);
  const [topology, setTopology] = useState<string>('all_to_all');
  const [shots, setShots] = useState<number>(1024);
  const [seed, setSeed] = useState<number>(42);

  // States for outputs
  const [compileResult, setCompileResult] = useState<any>(null);
  const [simResult, setSimResult] = useState<any>(null);
  const [distResult, setDistResult] = useState<any>(null);
  const [clusterInfo, setClusterInfo] = useState<any>(null);
  const [metaResults, setMetaResults] = useState<any>(null);
  const [faultResults, setFaultResults] = useState<any>(null);
  const [benchResults, setBenchResults] = useState<any>(null);
  const [cptpResult, setCptpResult] = useState<any>(null);
  const [noiseParam, setNoiseParam] = useState<number>(0.05);
  const [noiseChannel, setNoiseChannel] = useState<string>('depolarizing');
  const [protocol, setProtocol] = useState<string>('entanglement');
  const [protocolState, setProtocolState] = useState<string>('bell');
  const [protocolResult, setProtocolResult] = useState<any>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>('Ready');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const reportError = (error: unknown) => {
    const message = error instanceof ApiError
      ? `${error.message}${error.details ? ` Details: ${error.details}` : ''}`
      : error instanceof Error ? error.message : 'Unexpected application error.';
    setErrorMsg(message);
    setStatusMsg('Request failed');
  };

  useEffect(() => {
    fetchCluster();
    validateNoise(noiseChannel, noiseParam);
  }, []);

  const fetchCluster = async () => {
    try {
      setClusterInfo(await apiRequest('/api/cluster'));
    } catch (error) {
      reportError(error);
    }
  };

  const handleCompile = async () => {
    setLoading(true);
    setErrorMsg(null);
    setStatusMsg('Compiling and running optimization passes...');
    try {
      const data = await postJson('/api/compile', { code, opt_level: optLevel, topology });
      setCompileResult(data);
      setStatusMsg('Compilation complete');
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setErrorMsg(null);
    setStatusMsg(`Simulating on ${backend} backend...`);
    try {
      const data = await postJson('/api/run', { code, backend, shots, seed });
      setSimResult(data);
      setStatusMsg(`Simulation successful (${data.backend_used})`);
      if (activeTab === 'studio') setActiveTab('visualizer');
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDistributedRun = async () => {
    setLoading(true);
    setErrorMsg(null);
    setStatusMsg('Dispatching job to distributed worker cluster...');
    try {
      const data = await postJson('/api/distributed/run', { code, shots, seed });
      setDistResult(data);
      fetchCluster();
      setStatusMsg('Distributed execution completed with 95% confidence bounds');
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (type: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await postJson('/api/verify', { type });
      if (type === 'metamorphic') setMetaResults(data.results);
      if (type === 'fault_injection') setFaultResults(data);
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  const validateNoise = async (channel: string, param: number) => {
    try {
      const data = await postJson('/api/cptp/validate', { channel, param });
      setCptpResult(data.validation);
    } catch (error) {
      reportError(error);
    }
  };

  const runBenchmarks = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      setBenchResults(await apiRequest('/api/benchmarks'));
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  const runProtocol = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      let path = '/api/protocols/entanglement';
      let body: Record<string, unknown> = { state: protocolState };
      if (protocol === 'superdense') {
        path = '/api/protocols/superdense';
        body = { shots: 16, seed };
      } else if (protocol === 'teleportation') {
        path = '/api/protocols/teleportation';
        body = { alpha: [1 / Math.sqrt(2), 0], beta: [0, 1 / Math.sqrt(2)], shots: 32, seed };
      }
      setProtocolResult(await postJson(path, body));
      setStatusMsg('Protocol execution completed');
    } catch (error) {
      reportError(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#030712', color: '#f8fafc', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header */}
      <header style={{ borderBottom: '1px solid #1e293b', backgroundColor: '#0b1120', padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'linear-gradient(135deg, #06b6d4, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.05em', color: '#38bdf8' }}>INVARIANTQ</span>
              <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', backgroundColor: 'rgba(6, 182, 212, 0.2)', border: '1px solid #06b6d4', borderRadius: '4px', color: '#22d3ee' }}>v1.0 RESEARCH</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Adaptive Computing, Learning and Evaluation Platform</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
            <span>Status: <strong style={{ color: '#f8fafc' }}>{statusMsg}</strong></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
            <Server size={14} color="#06b6d4" />
            <span>Active Workers: <strong style={{ color: '#38bdf8' }}>{clusterInfo?.workers?.length ?? 'Unavailable'}</strong></span>
          </div>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav style={{ borderBottom: '1px solid #1e293b', backgroundColor: '#070d19', padding: '0 1.5rem', display: 'flex', gap: '1rem' }}>
        {[
          { id: 'studio', label: 'Circuit Studio', icon: Terminal },
          { id: 'visualizer', label: 'State Visualizer', icon: Activity },
          { id: 'noise', label: 'Noise & CPTP Lab', icon: Sliders },
          { id: 'cluster', label: 'Distributed Cluster', icon: Server },
          { id: 'verify', label: 'Verification & Metamorphic', icon: ShieldCheck },
          { id: 'benchmarks', label: 'Performance Benchmarks', icon: BarChart3 },
          { id: 'protocols', label: 'Quantum Protocols', icon: Atom }
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem 0.5rem',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? '#38bdf8' : '#94a3b8',
                borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                background: 'none',
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                cursor: 'pointer'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '1.5rem', maxWidth: '1600px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {errorMsg && (
          <div role="alert" style={{ marginBottom: '1rem', padding: '0.75rem 1rem', border: '1px solid #ef4444', borderRadius: '6px', backgroundColor: 'rgba(127, 29, 29, 0.3)', color: '#fecaca' }}>
            {errorMsg}
          </div>
        )}
        {activeTab === 'protocols' && (
          <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <h2 style={{ marginTop: 0, color: '#67e8f9' }}>Quantum Information Protocols</h2>
              <p style={{ color: '#94a3b8' }}>
                Execute the verified Python protocol service and inspect measured outcomes,
                reduced states, entropy, or teleportation fidelity.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
                <select value={protocol} onChange={(e) => setProtocol(e.target.value)}
                  style={{ backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', padding: '0.5rem' }}>
                  <option value="entanglement">Entanglement Explorer</option>
                  <option value="superdense">Superdense Coding</option>
                  <option value="teleportation">Quantum Teleportation</option>
                </select>
                {protocol === 'entanglement' && (
                  <select value={protocolState} onChange={(e) => setProtocolState(e.target.value)}
                    style={{ backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', padding: '0.5rem' }}>
                    <option value="product">Product state</option>
                    <option value="bell">Bell pair</option>
                    <option value="ghz">GHZ state</option>
                  </select>
                )}
                <button onClick={runProtocol} disabled={loading}
                  style={{ backgroundColor: '#0891b2', color: '#fff', border: 0, borderRadius: '4px', padding: '0.55rem 1rem', cursor: 'pointer' }}>
                  {loading ? 'Running...' : 'Run protocol'}
                </button>
              </div>
              {protocolResult && (
                <pre style={{ whiteSpace: 'pre-wrap', color: '#cbd5e1', backgroundColor: '#030712', padding: '1rem', borderRadius: '6px', overflowX: 'auto' }}>
                  {JSON.stringify(protocolResult, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
        {/* TAB 1: CIRCUIT STUDIO */}
        {activeTab === 'studio' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Terminal size={16} color="#38bdf8" /> IQ-Lang / OpenQASM Code Editor
                  </span>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select
                      onChange={(e) => setCode(PRESETS[e.target.value])}
                      style={{ backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                    >
                      {Object.keys(PRESETS).map(name => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  rows={14}
                  style={{
                    width: '100%',
                    backgroundColor: '#030712',
                    color: '#38bdf8',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '0.85rem',
                    padding: '0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #1e293b',
                    boxSizing: 'border-box',
                    resize: 'vertical'
                  }}
                />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
                      <span style={{ color: '#94a3b8' }}>Backend:</span>
                      <select
                        value={backend}
                        onChange={(e) => setBackend(e.target.value)}
                        style={{ backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                      >
                        <option value="adaptive">Adaptive Auto-Select (Heuristic)</option>
                        <option value="statevector">State-Vector (Exact 2^n)</option>
                        <option value="density_matrix">Density Matrix (CPTP Open-System)</option>
                        <option value="stabilizer">Stabilizer (Gottesman-Knill Clifford)</option>
                        <option value="tensor_network">Tensor Network (MPS SVD)</option>
                      </select>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
                      <span style={{ color: '#94a3b8' }}>Shots:</span>
                      <input
                        type="number"
                        value={shots}
                        onChange={(e) => setShots(Number(e.target.value))}
                        style={{ width: '80px', backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button
                      onClick={handleCompile}
                      disabled={loading}
                      style={{
                        backgroundColor: '#1e293b',
                        color: '#f8fafc',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        padding: '0.5rem 1rem',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                    >
                      <Layers size={15} color="#38bdf8" /> Compile Pass
                    </button>

                    <button
                      onClick={handleRun}
                      disabled={loading}
                      style={{
                        backgroundColor: '#0284c7',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '0.5rem 1.25rem',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                    >
                      <Play size={15} fill="#ffffff" /> Run Circuit
                    </button>
                  </div>
                </div>
              </div>

              {/* Compilation Details */}
              {compileResult && (
                <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#22d3ee', marginBottom: '0.75rem' }}>
                    Compiler Optimization Diagnostics
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '0.75rem' }}>
                    <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Gate Reduction</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>
                        {compileResult.original_gate_count} → {compileResult.optimized_gate_count}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Depth Reduction</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>
                        {compileResult.original_depth} → {compileResult.optimized_depth}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Semantic Check</div>
                      <div style={{ fontSize: '1rem', fontWeight: 600, color: compileResult.is_equivalent ? '#22c55e' : '#f87171' }}>
                        {compileResult.is_equivalent ? 'VERIFIED' : 'UNVERIFIED'}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Passes Applied</div>
                      <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                        {compileResult.passes_applied?.join(', ')}
                      </div>
                    </div>
                  </div>
                  <pre style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px', fontSize: '0.75rem', color: '#94a3b8', maxHeight: '140px', overflowY: 'auto' }}>
                    {compileResult.qasm}
                  </pre>
                </div>
              )}
            </div>

            {/* Quick Run & Results Sidebar */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '0.75rem' }}>
                  Execution Telemetry
                </div>
                {simResult ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1e293b', fontSize: '0.8rem' }}>
                      <span style={{ color: '#94a3b8' }}>Backend:</span>
                      <strong style={{ color: '#38bdf8' }}>{simResult.backend_used}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1e293b', fontSize: '0.8rem' }}>
                      <span style={{ color: '#94a3b8' }}>Runtime:</span>
                      <strong style={{ color: '#34d399' }}>{simResult.execution_time_ms.toFixed(3)} ms</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1e293b', fontSize: '0.8rem' }}>
                      <span style={{ color: '#94a3b8' }}>Memory Allocated:</span>
                      <strong style={{ color: '#f8fafc' }}>{(simResult.memory_used_bytes / 1024).toFixed(2)} KB</strong>
                    </div>
                    {simResult.entanglement_entropy !== null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1e293b', fontSize: '0.8rem' }}>
                        <span style={{ color: '#94a3b8' }}>Entanglement Entropy:</span>
                        <strong style={{ color: '#a78bfa' }}>{simResult.entanglement_entropy.toFixed(4)} bits</strong>
                      </div>
                    )}

                    <div style={{ marginTop: '1rem' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>
                        Measurement Distribution ({shots} shots)
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        {Object.entries(simResult.counts || {}).map(([bitstr, count]: any) => {
                          const pct = (count / shots) * 100;
                          return (
                            <div key={bitstr} style={{ fontSize: '0.75rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                                <span style={{ fontFamily: 'monospace' }}>|{bitstr}⟩</span>
                                <span>{count} ({pct.toFixed(1)}%)</span>
                              </div>
                              <div style={{ width: '100%', height: '6px', backgroundColor: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ width: `${pct}%`, height: '100%', backgroundColor: '#0ea5e9' }}></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                    Click "Run Circuit" to execute quantum evolution and inspect measurements.
                  </div>
                )}
              </div>

              {/* Distributed Execution Box */}
              <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>Distributed Multi-Node Execution</span>
                  <button
                    onClick={handleDistributedRun}
                    disabled={loading}
                    style={{ backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', borderRadius: '4px', padding: '0.3rem 0.75rem', fontSize: '0.75rem', cursor: 'pointer' }}
                  >
                    Dispatch Distributed
                  </button>
                </div>
                {distResult && (
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                    <div>Job ID: <strong style={{ color: '#f8fafc' }}>{distResult.job_id}</strong></div>
                    <div>Observable ⟨Z⟩: <strong style={{ color: '#38bdf8' }}>{distResult.z_expectation.toFixed(4)}</strong></div>
                    <div>95% CI: [{distResult.confidence_interval_95[0].toFixed(4)}, {distResult.confidence_interval_95[1].toFixed(4)}]</div>
                    <div>Recovery Events: <strong style={{ color: '#22c55e' }}>{distResult.fault_recovery_events}</strong></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: STATE VISUALIZER */}
        {activeTab === 'visualizer' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={18} /> Computational Basis Probability Distribution
              </div>
              {simResult?.probabilities ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {Object.entries(simResult.probabilities).map(([state, prob]: any) => (
                    <div key={state}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>|{state}⟩</span>
                        <span style={{ color: '#38bdf8' }}>{(prob * 100).toFixed(2)}% (prob: {prob.toFixed(4)})</span>
                      </div>
                      <div style={{ width: '100%', height: '14px', backgroundColor: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${prob * 100}%`, height: '100%', background: 'linear-gradient(90deg, #0284c7, #38bdf8)' }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
                  No simulation results yet. Run a circuit first.
                </div>
              )}
            </div>

            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Box size={18} /> State Vector Complex Amplitudes & Entanglement
              </div>
              {simResult?.amplitudes ? (
                <div>
                  <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px', fontSize: '0.85rem' }}>
                    <div>von Neumann Entanglement Entropy: <strong style={{ color: '#a78bfa' }}>{simResult.entanglement_entropy?.toFixed(4)} bits</strong></div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>Computed via bipartite cut partial trace diagonalization: S(ρ_A) = -Tr(ρ_A log2 ρ_A)</div>
                  </div>

                  <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #1e293b', textAlign: 'left', color: '#94a3b8' }}>
                          <th style={{ padding: '0.5rem' }}>Basis</th>
                          <th style={{ padding: '0.5rem' }}>Real</th>
                          <th style={{ padding: '0.5rem' }}>Imag</th>
                          <th style={{ padding: '0.5rem' }}>Phase</th>
                        </tr>
                      </thead>
                      <tbody>
                        {simResult.amplitudes.map((amp: any) => {
                          const phase = Math.atan2(amp.imag, amp.real);
                          return (
                            <tr key={amp.index} style={{ borderBottom: '1px solid #0f172a' }}>
                              <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>|{amp.bitstring}⟩</td>
                              <td style={{ padding: '0.5rem' }}>{amp.real.toFixed(4)}</td>
                              <td style={{ padding: '0.5rem' }}>{amp.imag.toFixed(4)}</td>
                              <td style={{ padding: '0.5rem', color: '#38bdf8' }}>{phase.toFixed(3)} rad</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
                  State amplitudes available when State-Vector backend is executed.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: NOISE & CPTP LAB */}
        {activeTab === 'noise' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '1rem' }}>
                Quantum Channel Configurator
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Noise Channel Formalism:</label>
                  <select
                    value={noiseChannel}
                    onChange={(e) => {
                      setNoiseChannel(e.target.value);
                      validateNoise(e.target.value, noiseParam);
                    }}
                    style={{ width: '100%', marginTop: '0.25rem', backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', padding: '0.5rem', fontSize: '0.85rem' }}
                  >
                    <option value="depolarizing">Depolarizing Channel (Isotropic Pauli Noise)</option>
                    <option value="amp_damping">Amplitude Damping (T1 Energy Relaxation)</option>
                    <option value="phase_damping">Phase Damping (T2 Pure Dephasing)</option>
                    <option value="bit_flip">Bit-Flip Channel (Pauli X)</option>
                    <option value="phase_flip">Phase-Flip Channel (Pauli Z)</option>
                  </select>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' }}>
                    <span>Error Probability / Decay Rate (p):</span>
                    <strong style={{ color: '#38bdf8' }}>{noiseParam.toFixed(3)}</strong>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={noiseParam}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setNoiseParam(val);
                      validateNoise(noiseChannel, val);
                    }}
                    style={{ width: '100%', marginTop: '0.5rem' }}
                  />
                </div>

                <div style={{ backgroundColor: '#030712', padding: '1rem', borderRadius: '6px', fontSize: '0.8rem', color: '#cbd5e1' }}>
                  <div style={{ fontWeight: 600, color: '#e2e8f0', marginBottom: '0.25rem' }}>Kraus Channel Representation:</div>
                  <div style={{ fontFamily: 'monospace', color: '#38bdf8' }}>
                    ℰ(ρ) = ∑_k K_k ρ K_k†, with ∑_k K_k† K_k = I
                  </div>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                    Verified via Choi-Jamiolkowski isomorphism J(ℰ) = (I ⊗ ℰ)(|Φ+⟩⟨Φ+|). Complete positivity guaranteed by J(ℰ) ≥ 0.
                  </div>
                </div>
              </div>
            </div>

            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '1rem' }}>
                Mathematical CPTP Verification
              </div>
              {cptpResult ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px' }}>
                    <span style={{ fontSize: '0.85rem' }}>Completely Positive (CP):</span>
                    <span style={{ color: cptpResult.is_completely_positive ? '#22c55e' : '#f87171', fontWeight: 600 }}>
                      {cptpResult.is_completely_positive ? 'VALID (λ_min ≥ 0)' : 'VIOLATION'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px' }}>
                    <span style={{ fontSize: '0.85rem' }}>Trace-Preserving (TP):</span>
                    <span style={{ color: cptpResult.is_trace_preserving ? '#22c55e' : '#f87171', fontWeight: 600 }}>
                      {cptpResult.is_trace_preserving ? 'VALID (∑ K†K = I)' : 'VIOLATION'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px' }}>
                    <span style={{ fontSize: '0.85rem' }}>Choi Matrix Min Eigenvalue:</span>
                    <span style={{ fontFamily: 'monospace', color: '#38bdf8' }}>
                      {cptpResult.choi_min_eigenvalue.toExponential(4)}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px' }}>
                    <span style={{ fontSize: '0.85rem' }}>Trace Residual ||∑ K†K - I||:</span>
                    <span style={{ fontFamily: 'monospace', color: '#38bdf8' }}>
                      {cptpResult.trace_preserving_residual.toExponential(4)}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#030712', borderRadius: '6px' }}>
                    <span style={{ fontSize: '0.85rem' }}>Random Density Preservation:</span>
                    <span style={{ color: cptpResult.random_density_tests_passed ? '#22c55e' : '#f87171', fontWeight: 600 }}>
                      {cptpResult.random_density_tests_passed ? '10/10 PASSED' : 'FAILED'}
                    </span>
                  </div>
                </div>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
                  Validating channel...
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: DISTRIBUTED CLUSTER */}
        {activeTab === 'cluster' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#38bdf8' }}>Distributed Execution Orchestrator</h2>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Network-aware shot partitioning and automatic failover ledger (Cisco 2025 / Caleffi 2024 architecture)</div>
              </div>
              <button
                onClick={fetchCluster}
                style={{ backgroundColor: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', padding: '0.5rem 1rem', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <RefreshCw size={14} /> Refresh Nodes
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
              {clusterInfo?.workers?.map((w: any) => (
                <div key={w.id} style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, color: '#f8fafc' }}>{w.id}</span>
                    <span style={{
                      fontSize: '0.7rem',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '4px',
                      backgroundColor: w.status === 'IDLE' ? 'rgba(34, 197, 94, 0.2)' : w.status === 'BUSY' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: w.status === 'IDLE' ? '#22c55e' : w.status === 'BUSY' ? '#38bdf8' : '#ef4444'
                    }}>
                      {w.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div>Host: <span style={{ color: '#cbd5e1' }}>{w.host}</span></div>
                    <div>Cores: <span style={{ color: '#cbd5e1' }}>{w.cores}</span></div>
                    <div>Tasks Completed: <strong style={{ color: '#38bdf8' }}>{w.tasks_completed}</strong></div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '0.5rem' }}>
                Deterministic Seed Tree & Fault Tolerance Proof
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
                Each task receives a deterministic pseudorandom seed derived from <code style={{ color: '#38bdf8' }}>SHA-256(master_seed : job_id : task_idx)</code>.
                When a worker crashes mid-task, the scheduler detects heartbeat loss, immediately retries the task on another worker with the exact same seed,
                guaranteeing identical statistical convergence without bias or dropped measurement samples.
              </p>
            </div>
          </div>
        )}

        {/* TAB 5: VERIFICATION & METAMORPHIC */}
        {activeTab === 'verify' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8' }}>Metamorphic Invariant Suite</span>
                <button
                  onClick={() => handleVerify('metamorphic')}
                  disabled={loading}
                  style={{ backgroundColor: '#0284c7', color: '#ffffff', border: 'none', borderRadius: '4px', padding: '0.4rem 0.8rem', fontSize: '0.8rem', cursor: 'pointer' }}
                >
                  Run Metamorphic Suite
                </button>
              </div>

              {metaResults ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {metaResults.map((r: any, idx: number) => (
                    <div key={idx} style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px', borderLeft: `3px solid ${r.passed ? '#22c55e' : '#ef4444'}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{r.relation}</span>
                        <span style={{ color: r.passed ? '#22c55e' : '#ef4444', fontWeight: 600, fontSize: '0.8rem' }}>
                          {r.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{r.details}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
                  Click "Run Metamorphic Suite" to verify Chen (2018) relation invariants.
                </div>
              )}
            </div>

            <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8' }}>Fault Injection & Flaw Detection</span>
                <button
                  onClick={() => handleVerify('fault_injection')}
                  disabled={loading}
                  style={{ backgroundColor: '#ef4444', color: '#ffffff', border: 'none', borderRadius: '4px', padding: '0.4rem 0.8rem', fontSize: '0.8rem', cursor: 'pointer' }}
                >
                  Inject Flaw & Detect
                </button>
              </div>

              {faultResults ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Corrupted Gate Mutation:</span>
                      <span style={{ color: faultResults.corrupted_gate_caught ? '#22c55e' : '#ef4444', fontWeight: 600 }}>
                        {faultResults.corrupted_gate_caught ? 'CAUGHT & FLAGGED' : 'UNDETECTED'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{faultResults.details}</div>
                  </div>

                  <div style={{ backgroundColor: '#030712', padding: '0.75rem', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Broken CPTP Channel Mutation:</span>
                      <span style={{ color: faultResults.broken_cptp_caught ? '#22c55e' : '#ef4444', fontWeight: 600 }}>
                        {faultResults.broken_cptp_caught ? 'CAUGHT & FLAGGED' : 'UNDETECTED'}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Detected non-trace-preserving Kraus operator set</div>
                  </div>
                </div>
              ) : (
                <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
                  Click "Inject Flaw & Detect" to demonstrate that the test suite detects corrupted gates and invalid channels.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 6: PERFORMANCE BENCHMARKS */}
        {activeTab === 'benchmarks' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#38bdf8' }}>Performance & Scaling Benchmarks</h2>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Empirical verification of NWQ-Sim gate fusion speedup and multi-qubit memory scaling</div>
              </div>
              <button
                onClick={runBenchmarks}
                disabled={loading}
                style={{ backgroundColor: '#0284c7', color: '#ffffff', border: 'none', borderRadius: '6px', padding: '0.5rem 1rem', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                Run Live Benchmarks
              </button>
            </div>

            {benchResults ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '0.75rem' }}>
                    Gate Fusion Speedup Results
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <div>Circuit: 14 Qubits, 24 Layers</div>
                    <div>Original Ops: <strong>{benchResults.fusion.unfused_ops}</strong> → Fused Ops: <strong style={{ color: '#38bdf8' }}>{benchResults.fusion.fused_ops}</strong></div>
                    <div>Fusion Groups: <strong>{benchResults.fusion.fusion_groups}</strong></div>
                    <div>Unfused Runtime: {benchResults.fusion.unfused_time_ms.toFixed(2)} ms</div>
                    <div>Fused Runtime: <strong style={{ color: '#22c55e' }}>{benchResults.fusion.fused_time_ms.toFixed(2)} ms</strong></div>
                    <div>Speedup Ratio: <strong style={{ color: '#22d3ee' }}>{benchResults.fusion.speedup_ratio.toFixed(2)}x</strong></div>
                  </div>
                </div>

                <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '0.75rem' }}>
                    State-Vector Qubit Scaling
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #1e293b', textAlign: 'left', color: '#94a3b8' }}>
                        <th style={{ padding: '0.4rem' }}>Qubits</th>
                        <th style={{ padding: '0.4rem' }}>Dimension</th>
                        <th style={{ padding: '0.4rem' }}>Memory</th>
                        <th style={{ padding: '0.4rem' }}>Runtime</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchResults.scaling?.map((row: any) => (
                        <tr key={row.num_qubits} style={{ borderBottom: '1px solid #0f172a' }}>
                          <td style={{ padding: '0.4rem', fontWeight: 600 }}>{row.num_qubits} Q</td>
                          <td style={{ padding: '0.4rem' }}>{row.dimension.toLocaleString()}</td>
                          <td style={{ padding: '0.4rem' }}>{(row.memory_bytes / 1024).toFixed(1)} KB</td>
                          <td style={{ padding: '0.4rem', color: '#38bdf8' }}>{row.execution_time_ms.toFixed(2)} ms</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div style={{ backgroundColor: '#0b1120', border: '1px solid #1e293b', borderRadius: '8px', padding: '3rem', textAlign: 'center', color: '#64748b' }}>
                Click "Run Live Benchmarks" to quantify multi-qubit runtime scaling and NWQ-Sim gate fusion acceleration.
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid #1e293b', backgroundColor: '#0b1120', padding: '0.75rem 1.5rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b' }}>
        <span>INVARIANTQ © 2026. Fully open-source under Apache-2.0 / MIT.</span>
        <span>Hybrid C++ Numerical Engine + Python Orchestration + React Studio</span>
      </footer>
    </div>
  );
}
