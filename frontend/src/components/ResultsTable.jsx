import { Download, Users, Phone, MapPin, Copy, Check } from 'lucide-react';
import { useState } from 'react';

export default function ResultsTable({ results, onExport, city }) {
    const [copiedId, setCopiedId] = useState(null);

    const handleCopy = (row) => {
        const text = `Nome: ${row.companyName}\nContato: ${row.phone || 'Não encontrado'}\nEndereço: ${row.address}\nCidade: ${city || ''}`;
        navigator.clipboard.writeText(text).then(() => {
            setCopiedId(row.id);
            setTimeout(() => setCopiedId(null), 2000);
        });
    };

    if (!results || results.length === 0) return null;

    return (
        <div className="glass-panel animate-fade-in" style={{ animationDelay: '0.2s', marginTop: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h2>Resultados da Prospecção</h2>
                    <p>Encontrados <span className="badge">{results.length} contatos</span></p>
                </div>
                <button className="btn-secondary" onClick={onExport}>
                    <Download size={18} />
                    Exportar CSV
                </button>
            </div>

            <div className="table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Users size={16} /> Empresa</div></th>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Phone size={16} /> Contato</div></th>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><MapPin size={16} /> Endereço</div></th>
                            <th style={{ width: '100px', textAlign: 'center' }}>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((row) => (
                            <tr key={row.id}>
                                <td style={{ fontWeight: 500, color: 'var(--text-main)' }}>{row.companyName}</td>
                                <td>{row.phone || <span style={{ color: 'var(--text-muted)' }}>Não encontrado</span>}</td>
                                <td>{row.address}</td>
                                <td style={{ textAlign: 'center' }}>
                                    <button
                                        className="btn-secondary"
                                        style={{ padding: '0.4rem', border: 'none', background: 'rgba(255,255,255,0.05)' }}
                                        onClick={() => handleCopy(row)}
                                        title="Copiar informações"
                                    >
                                        {copiedId === row.id ? <Check size={16} color="#4ade80" /> : <Copy size={16} />}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
