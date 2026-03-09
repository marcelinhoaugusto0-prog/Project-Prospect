import { Download, Users, Phone, MapPin, Copy, Check, Star, Globe, Tag } from 'lucide-react';
import { useState } from 'react';

export default function ResultsTable({ results, onExport, city }) {
    const [copiedId, setCopiedId] = useState(null);

    const handleCopy = (row) => {
        const lines = [
            `Nome: ${row.companyName}`,
            `Contato: ${row.phone || 'Não encontrado'}`,
            `Endereço: ${row.address || ''}`,
            row.website ? `Site: ${row.website}` : '',
            row.rating ? `Avaliação: ${row.rating}⭐ (${row.reviews || 0} avaliações)` : '',
            row.category ? `Categoria: ${row.category}` : '',
        ].filter(Boolean).join('\n');

        navigator.clipboard.writeText(lines).then(() => {
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
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Star size={16} /> Avaliação</div></th>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Globe size={16} /> Site</div></th>
                            <th style={{ width: '80px', textAlign: 'center' }}>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((row) => (
                            <tr key={row.id}>
                                <td style={{ fontWeight: 500, color: 'var(--text-main)' }}>
                                    {row.companyName}
                                    {row.category && (
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Tag size={10} /> {row.category}
                                        </div>
                                    )}
                                </td>
                                <td>{row.phone || <span style={{ color: 'var(--text-muted)' }}>Não encontrado</span>}</td>
                                <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.address}</td>
                                <td>
                                    {row.rating ? (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Star size={14} fill="#fbbf24" color="#fbbf24" />
                                            <span style={{ fontWeight: 600 }}>{row.rating}</span>
                                            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({row.reviews || 0})</span>
                                        </div>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                                    )}
                                </td>
                                <td>
                                    {row.website ? (
                                        <a href={row.website} target="_blank" rel="noopener noreferrer"
                                            style={{ color: 'var(--accent)', textDecoration: 'none', fontSize: '0.85rem' }}>
                                            Visitar ↗
                                        </a>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                                    )}
                                </td>
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
