import { useState } from 'react';
import SearchForm from './components/SearchForm';
import ResultsTable from './components/ResultsTable';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [lastSearchedCity, setLastSearchedCity] = useState('');

  const handleSearch = async ({ segment, location, radius, city }) => {
    setIsLoading(true);
    setError(null);
    setResults([]);
    if (city) setLastSearchedCity(city);
    else setLastSearchedCity(location || '');

    try {
      // Endpoint logic: Calls Python backend API
      const response = await fetch('/api/prospects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ segment, location, radius }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail || 'Falha na comunicação com o servidor de automação.';
        throw new Error(detail);
      }

      const data = await response.json();
      setResults(data.data || []);
    } catch (err) {
      setError(err.message || 'Erro inesperado ao buscar contatos.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    const headers = ['Empresa', 'Telefone', 'Endereço', 'Site', 'Avaliação', 'Avaliações', 'Categoria'];
    const rows = results.map(r => [
      `"${(r.companyName || '').replace(/"/g, '""')}"`,
      r.phone || 'Não encontrado',
      `"${(r.address || '').replace(/"/g, '""')}"`,
      r.website || '',
      r.rating || '',
      r.reviews || '',
      `"${(r.category || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8,"
      + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "prospects.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="app-container">
      <header className="dashboard-header animate-fade-in">
        <h1>Prospect Automator</h1>
        <p>Gere listas de contatos qualificados 100% no automático.</p>
      </header>

      <main className="dashboard-grid">
        {/* Sidebar/Search */}
        <div>
          <SearchForm onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Main Content Area */}
        <div>
          {isLoading && (
            <div className="loader-container animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="loader loader-large"></div>
              <div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Buscando Prospects...</h3>
                <p>Nossa automação está varrendo a região em busca dos melhores contatos para você.</p>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="glass-panel animate-fade-in" style={{ borderColor: 'rgba(239, 68, 68, 0.5)', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
              <h3 style={{ color: '#f87171', marginBottom: '0.5rem' }}>Erro na Automação</h3>
              <p>{error}</p>
            </div>
          )}

          {!isLoading && results.length > 0 && (
            <ResultsTable results={results} onExport={handleExportCSV} city={lastSearchedCity} />
          )}

          {!isLoading && results.length === 0 && !error && (
            <div className="glass-panel animate-fade-in" style={{ textAlign: 'center', opacity: 0.7, padding: '4rem 2rem' }}>
              <p>Preencha os dados e clique em "Gerar Prospects" para iniciar a automação.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
