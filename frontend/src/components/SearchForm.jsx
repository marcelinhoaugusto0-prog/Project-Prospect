import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

export default function SearchForm({ onSearch, isLoading }) {
  const [segment, setSegment] = useState('');

  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);

  const [selectedState, setSelectedState] = useState('');
  const [selectedCity, setSelectedCity] = useState('');

  const [radius, setRadius] = useState(10);

  useEffect(() => {
    fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome')
      .then(res => res.json())
      .then(data => setStates(data))
      .catch(err => console.error("Erro ao carregar estados:", err));
  }, []);

  useEffect(() => {
    if (!selectedState) {
      setCities([]);
      setSelectedCity('');
      return;
    }
    fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${selectedState}/municipios?orderBy=nome`)
      .then(res => res.json())
      .then(data => setCities(data))
      .catch(err => console.error("Erro ao carregar municípios:", err));
  }, [selectedState]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!segment || !selectedCity || !selectedState) return;

    const stateObj = states.find(s => s.sigla === selectedState);
    const cityObj = cities.find(c => c.id.toString() === selectedCity);

    const cityName = cityObj ? cityObj.nome : '';
    const stateName = stateObj ? stateObj.sigla : '';

    const location = `${cityName}, ${stateName}`;

    onSearch({ segment, location, city: cityName, state: stateName, radius });
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.1s' }}>
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Search size={22} color="var(--primary-color)" />
        Nova Prospecção
      </h2>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label className="input-label" htmlFor="segment">Segmento de Mercado</label>
          <input
            id="segment"
            type="text"
            className="glass-input"
            placeholder="Ex: Clínicas Odontológicas, Restaurantes..."
            value={segment}
            onChange={(e) => setSegment(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="state">Estado (UF)</label>
          <select
            id="state"
            className="glass-input"
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            required
            disabled={isLoading || states.length === 0}
          >
            <option value="">Selecione um estado</option>
            {states.map(s => (
              <option key={s.id} value={s.sigla}>{s.nome} ({s.sigla})</option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="city">Cidade</label>
          <select
            id="city"
            className="glass-input"
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            required
            disabled={isLoading || !selectedState || cities.length === 0}
          >
            <option value="">Selecione uma cidade</option>
            {cities.map(c => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </div>

        <div className="input-group">
          <label className="input-label" htmlFor="radius">
            Raio de Busca: <span style={{ color: 'var(--primary-color)', fontWeight: 'bold' }}>{radius} km</span>
          </label>
          <input
            id="radius"
            type="range"
            min="1"
            max="100"
            className="range-slider"
            value={radius}
            onChange={(e) => setRadius(parseInt(e.target.value))}
            disabled={isLoading}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>1 km</span>
            <span>100 km</span>
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={isLoading || !segment || !selectedCity || !selectedState}
        >
          {isLoading ? (
            <>
              <div className="loader" style={{ width: '18px', height: '18px', borderWidth: '2px' }}></div>
              Prospecção em andamento...
            </>
          ) : (
            <>Gerar Prospects</>
          )}
        </button>
      </form>
    </div>
  );
}
