import { useState } from 'react';
import SearchForm from './components/SearchForm';
import ResultsTable from './components/ResultsTable';
import InstagramResults from './components/InstagramResults';

function App() {
  const [searchMode, setSearchMode] = useState('maps'); // 'maps' or 'instagram'
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [igResults, setIgResults] = useState([]);
  const [error, setError] = useState(null);
  const [lastSearchedCity, setLastSearchedCity] = useState('');

  // OpenStreetMap search
  const handleSearch = async ({ segment, location, radius, city }) => {
    setIsLoading(true);
    setError(null);
    setResults([]);
    if (city) setLastSearchedCity(city);
    else setLastSearchedCity(location || '');

    try {
      const response = await fetch('/api/prospects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment, location, radius }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail || 'Falha na comunicação com o servidor.';
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

  // Instagram hashtag search
  const handleInstagramSearch = async (hashtag) => {
    setIsLoading(true);
    setError(null);
    setIgResults([]);

    try {
      const response = await fetch('/api/instagram-prospects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hashtag }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail || 'Falha na busca do Instagram.';
        throw new Error(detail);
      }

      const data = await response.json();
      setIgResults(data.data || []);
    } catch (err) {
      setError(err.message || 'Erro inesperado ao buscar no Instagram.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (searchMode === 'instagram') {
      // Instagram CSV
      const headers = ['Username', 'Nome', 'Telefone', 'Bio', 'Site', 'Link Perfil'];
      const rows = igResults.map(r => [
        r.username || '',
        `"${(r.name || '').replace(/"/g, '""')}"`,
        r.phone || '',
        `"${(r.bio || '').replace(/"/g, '""')}"`,
        r.website || '',
        r.profileLink || '',
      ]);
      const csvContent = "data:text/csv;charset=utf-8,"
        + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      const link = document.createElement("a");
      link.setAttribute("href", encodeURI(csvContent));
      link.setAttribute("download", "instagram_prospects.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      // Maps CSV
      const headers = ['Empresa', 'Telefone', 'Endereço', 'Site', 'Categoria'];
      const rows = results.map(r => [
        `"${(r.companyName || '').replace(/"/g, '""')}"`,
        r.phone || 'Não encontrado',
        `"${(r.address || '').replace(/"/g, '""')}"`,
        r.website || '',
        `"${(r.category || '').replace(/"/g, '""')}"`,
      ]);
      const csvContent = "data:text/csv;charset=utf-8,"
        + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      const link = document.createElement("a");
      link.setAttribute("href", encodeURI(csvContent));
      link.setAttribute("download", "prospects.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const activeResults = searchMode === 'instagram' ? igResults : results;

  return (
    <div className="app-container">
      <header className="dashboard-header animate-fade-in">
        <h1>Prospect Automator</h1>
        <p>Gere listas de contatos qualificados 100% no automático.</p>

        {/* Tab Toggle */}
        <div style={{
          display: 'flex', gap: '0', marginTop: '1rem',
          background: 'rgba(255,255,255,0.05)', borderRadius: '12px',
          padding: '4px', width: 'fit-content', margin: '1rem auto 0',
        }}>
          <button
            onClick={() => { setSearchMode('maps'); setError(null); }}
            style={{
              padding: '0.6rem 1.5rem', borderRadius: '10px', border: 'none',
              cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem',
              transition: 'all 0.3s ease',
              background: searchMode === 'maps' ? 'var(--accent)' : 'transparent',
              color: searchMode === 'maps' ? '#fff' : 'var(--text-muted)',
            }}
          >
            🗺️ Google Maps
          </button>
          <button
            onClick={() => { setSearchMode('instagram'); setError(null); }}
            style={{
              padding: '0.6rem 1.5rem', borderRadius: '10px', border: 'none',
              cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem',
              transition: 'all 0.3s ease',
              background: searchMode === 'instagram' ? 'linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)' : 'transparent',
              color: searchMode === 'instagram' ? '#fff' : 'var(--text-muted)',
            }}
          >
            📸 Instagram
          </button>
        </div>
      </header>

      <main className="dashboard-grid">
        {/* Sidebar/Search */}
        <div>
          {searchMode === 'maps' ? (
            <SearchForm onSearch={handleSearch} isLoading={isLoading} />
          ) : (
            <div className="glass-panel animate-fade-in">
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                📸 Busca no Instagram
              </h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                Busque por hashtags e encontre empresas com contato na bio.
              </p>
              <form onSubmit={(e) => {
                e.preventDefault();
                const hashtag = e.target.hashtag.value.trim();
                if (hashtag) handleInstagramSearch(hashtag);
              }}>
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Hashtag
                  </label>
                  <input
                    name="hashtag"
                    type="text"
                    placeholder="Ex: padaria, clinicaodontologica, pizzaria"
                    style={{
                      width: '100%', padding: '0.75rem 1rem', borderRadius: '10px',
                      border: '1px solid rgba(255,255,255,0.1)',
                      background: 'rgba(255,255,255,0.05)', color: 'var(--text-main)',
                      fontSize: '1rem', boxSizing: 'border-box',
                    }}
                  />
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.4rem' }}>
                    Não precisa colocar #. O bot analisa a bio e mostra só perfis com telefone ou site.
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn-primary"
                  style={{ width: '100%', opacity: isLoading ? 0.6 : 1 }}
                >
                  {isLoading ? 'Buscando...' : '🔍 Buscar no Instagram'}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Main Content Area */}
        <div>
          {isLoading && (
            <div className="loader-container animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="loader loader-large"></div>
              <div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
                  {searchMode === 'instagram' ? 'Analisando perfis do Instagram...' : 'Buscando Prospects...'}
                </h3>
                <p>
                  {searchMode === 'instagram'
                    ? 'O bot está analisando bios e extraindo contatos de cada perfil.'
                    : 'Nossa automação está varrendo a região em busca dos melhores contatos.'}
                </p>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="glass-panel animate-fade-in" style={{ borderColor: 'rgba(239, 68, 68, 0.5)', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
              <h3 style={{ color: '#f87171', marginBottom: '0.5rem' }}>Erro na Automação</h3>
              <p>{error}</p>
            </div>
          )}

          {!isLoading && searchMode === 'maps' && results.length > 0 && (
            <ResultsTable results={results} onExport={handleExportCSV} city={lastSearchedCity} />
          )}

          {!isLoading && searchMode === 'instagram' && igResults.length > 0 && (
            <InstagramResults results={igResults} onExport={handleExportCSV} />
          )}

          {!isLoading && activeResults.length === 0 && !error && (
            <div className="glass-panel animate-fade-in" style={{ textAlign: 'center', opacity: 0.7, padding: '4rem 2rem' }}>
              <p>
                {searchMode === 'instagram'
                  ? 'Digite uma hashtag e clique em "Buscar no Instagram" para encontrar empresas com contato na bio.'
                  : 'Preencha os dados e clique em "Gerar Prospects" para iniciar a automação.'}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
