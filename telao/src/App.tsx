import { useState, useEffect } from 'react';
import Arena from './components/Arena';
import Voting from './components/Voting';
import Scoreboard from './components/Scoreboard';
import { AdminPanel } from './components/AdminPanel';

function App() {
  const [view, setView] = useState<'arena' | 'voting' | 'scoreboard' | 'admin'>('arena');
  const params = new URLSearchParams(window.location.search);
  const initialView = params.get('view') as 'arena' | 'voting' | 'scoreboard' | 'admin' | null;

  useEffect(() => {
    if (initialView) {
      setView(initialView);
    }
  }, [initialView]);

  const renderView = () => {
    switch (view) {
      case 'voting':
        return <Voting />;
      case 'scoreboard':
        return <Scoreboard />;
      case 'admin':
        return <AdminPanel />;
      default:
        return <Arena />;
    }
  };

  return (
    <div className="min-h-screen bg-dark">
      {renderView()}
    </div>
  );
}

export default App;
