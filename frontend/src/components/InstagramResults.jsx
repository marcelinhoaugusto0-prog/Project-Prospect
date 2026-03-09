import { Download, AtSign, Phone, Globe, Copy, Check, ExternalLink } from 'lucide-react';
import { useState } from 'react';

export default function InstagramResults({ results, onExport }) {
    const [copiedId, setCopiedId] = useState(null);

    const handleCopy = (row) => {
        const lines = [
            `Username: ${row.username}`,
            `Nome: ${row.name || ''}`,
            row.phone ? `Telefone: ${row.phone}` : '',
            row.website ? `Site: ${row.website}` : '',
            `Perfil: ${row.profileLink}`,
            row.bio ? `Bio: ${row.bio}` : '',
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
                    <h2>📸 Resultados do Instagram</h2>
                    <p>Encontrados <span className="badge">{results.length} perfis com contato</span></p>
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
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><AtSign size={16} /> Usuário</div></th>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Phone size={16} /> Telefone</div></th>
                            <th style={{ maxWidth: '300px' }}>Bio</th>
                            <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Globe size={16} /> Site</div></th>
                            <th style={{ width: '80px', textAlign: 'center' }}>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((row) => (
                            <tr key={row.id}>
                                <td style={{ fontWeight: 500, color: 'var(--text-main)' }}>
                                    <a href={row.profileLink} target="_blank" rel="noopener noreferrer"
                                        style={{ color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                        {row.username} <ExternalLink size={12} />
                                    </a>
                                    {row.name && row.name !== row.username?.replace('@', '') && (
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                                            {row.name}
                                        </div>
                                    )}
                                </td>
                                <td style={{ fontWeight: 600, color: row.phone ? '#4ade80' : 'var(--text-muted)' }}>
                                    {row.phone || '—'}
                                </td>
                                <td style={{ maxWidth: '300px', fontSize: '0.8rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {row.bio || '—'}
                                </td>
                                <td>
                                    {row.website ? (
                                        <a href={row.website.startsWith('http') ? row.website : `https://${row.website}`}
                                            target="_blank" rel="noopener noreferrer"
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
