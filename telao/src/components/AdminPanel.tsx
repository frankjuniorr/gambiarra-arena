import { useState, useEffect } from 'react';

interface Session {
  id: string;
  pin: string;
  status: string;
  createdAt: string;
}

interface Round {
  id: string;
  sessionId: string;
  prompt: string;
  maxTokens: number;
  temperature: number;
  status: string;
  createdAt: string;
}

export function AdminPanel() {
  const [session, setSession] = useState<Session | null>(null);
  const [rounds, setRounds] = useState<Round[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [newPrompt, setNewPrompt] = useState('');
  const [maxTokens, setMaxTokens] = useState(500);
  const [temperature, setTemperature] = useState(0.7);
  const [deadlineMs, setDeadlineMs] = useState(120000);

  const API_BASE = 'http://localhost:3000';

  useEffect(() => {
    loadSession();
  }, []);

  const loadSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/session`);
      if (response.ok) {
        const data = await response.json();
        setSession(data);
        loadRounds(data.id);
      }
    } catch (err) {
      console.error('Error loading session:', err);
    }
  };

  const loadRounds = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE}/session`);
      if (response.ok) {
        const data = await response.json();
        console.log('Session data:', data);
        setRounds(data.rounds || []);
      }
    } catch (err) {
      console.error('Error loading rounds:', err);
    }
  };

  const createSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        setSession(data);
        alert(`Sessão criada! PIN: ${data.pin}`);
      } else {
        setError('Erro ao criar sessão');
      }
    } catch (err) {
      setError('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const createRound = async () => {
    if (!session) {
      setError('Crie uma sessão primeiro');
      return;
    }
    if (!newPrompt.trim()) {
      setError('Digite um prompt');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/rounds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: session.id,
          prompt: newPrompt,
          maxTokens,
          temperature,
          deadlineMs,
          seed: Math.floor(Math.random() * 1000000)
        })
      });
      if (response.ok) {
        const data = await response.json();
        setRounds([...rounds, data]);
        setNewPrompt('');
        alert('Rodada criada com sucesso!');
      } else {
        setError('Erro ao criar rodada');
      }
    } catch (err) {
      setError('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const startRound = async (roundId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/rounds/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roundId })
      });
      if (response.ok) {
        alert('Rodada iniciada!');
        loadSession();
      } else {
        setError('Erro ao iniciar rodada');
      }
    } catch (err) {
      setError('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const stopRound = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/rounds/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        alert('Rodada parada!');
        loadSession();
      } else {
        setError('Erro ao parar rodada');
      }
    } catch (err) {
      setError('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Admin Panel - Gambiarra Club</h1>

        {error && (
          <div className="bg-red-600 text-white p-4 rounded mb-4">
            {error}
          </div>
        )}

        {/* Session Section */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Sessão</h2>
          {session ? (
            <div>
              <p className="mb-2"><strong>ID:</strong> {session.id}</p>
              <p className="mb-2"><strong>PIN:</strong> <span className="text-green-400 text-2xl font-mono">{session.pin}</span></p>
              <p className="mb-2"><strong>Status:</strong> {session.status}</p>
            </div>
          ) : (
            <div>
              <p className="mb-4">Nenhuma sessão ativa</p>
              <button
                onClick={createSession}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded font-bold disabled:opacity-50"
              >
                Criar Nova Sessão
              </button>
            </div>
          )}
        </div>

        {/* Create Round Section */}
        {session && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Criar Nova Rodada</h2>
            <div className="space-y-4">
              <div>
                <label className="block mb-2">Prompt:</label>
                <textarea
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  className="w-full bg-gray-700 text-white p-3 rounded"
                  rows={4}
                  placeholder="Digite o desafio para os participantes..."
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block mb-2">Max Tokens:</label>
                  <input
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(Number(e.target.value))}
                    className="w-full bg-gray-700 text-white p-2 rounded"
                  />
                </div>
                <div>
                  <label className="block mb-2">Temperature:</label>
                  <input
                    type="number"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(Number(e.target.value))}
                    className="w-full bg-gray-700 text-white p-2 rounded"
                  />
                </div>
                <div>
                  <label className="block mb-2">Deadline (ms):</label>
                  <input
                    type="number"
                    value={deadlineMs}
                    onChange={(e) => setDeadlineMs(Number(e.target.value))}
                    className="w-full bg-gray-700 text-white p-2 rounded"
                  />
                </div>
              </div>
              <button
                onClick={createRound}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-bold disabled:opacity-50"
              >
                Criar Rodada
              </button>
            </div>
          </div>
        )}

        {/* Rounds List */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Rodadas</h2>
            {session && (
              <button
                onClick={() => loadRounds(session.id)}
                disabled={loading}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded text-sm font-bold disabled:opacity-50"
              >
                🔄 Recarregar
              </button>
            )}
          </div>
          {rounds.length === 0 ? (
            <p className="text-gray-400">Nenhuma rodada criada ainda</p>
          ) : (
            <div className="space-y-4">
              {rounds.map((round) => (
                <div key={round.id} className="bg-gray-700 p-4 rounded">
                  <div className="mb-3">
                    <p className="text-sm text-gray-400">ID: {round.id}</p>
                    <p className="font-bold text-lg mt-1">{round.prompt}</p>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-sm mb-3">
                    <p><strong>Status:</strong> <span className={
                      round.status === 'active' ? 'text-green-400' :
                      round.status === 'pending' ? 'text-yellow-400' :
                      'text-gray-400'
                    }>{round.status}</span></p>
                    <p><strong>Tokens:</strong> {round.maxTokens}</p>
                    <p><strong>Temp:</strong> {round.temperature}</p>
                    <p><strong>Deadline:</strong> {round.deadlineMs || deadlineMs}ms</p>
                  </div>
                  <div className="flex gap-2">
                    {round.status === 'pending' && (
                      <button
                        onClick={() => startRound(round.id)}
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm font-bold disabled:opacity-50"
                      >
                        ▶️ Iniciar Rodada
                      </button>
                    )}
                    {round.status === 'active' && (
                      <button
                        onClick={stopRound}
                        disabled={loading}
                        className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm font-bold disabled:opacity-50"
                      >
                        ⏹️ Parar Rodada
                      </button>
                    )}
                    {round.status === 'completed' && (
                      <span className="text-gray-400 px-4 py-2">✅ Concluída</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6">
          <a href="/" className="text-blue-400 hover:text-blue-300">← Voltar para o Telão</a>
        </div>
      </div>
    </div>
  );
}
