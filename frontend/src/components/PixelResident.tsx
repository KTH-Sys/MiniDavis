import type { CSSProperties } from 'react';

const palettes: Record<string, { hair: string; skin: string; shirt: string; accent: string }> = {
  ethan: { hair: '#503225', skin: '#dba579', shirt: '#c24e42', accent: '#efba64' },
  gayatri: { hair: '#382b29', skin: '#be8259', shirt: '#b88b37', accent: '#f2d583' },
  aishani: { hair: '#302931', skin: '#c99169', shirt: '#8664b0', accent: '#d4b4df' },
  rylee: { hair: '#664332', skin: '#e6b592', shirt: '#4f91aa', accent: '#b1d9d3' },
  saurya: { hair: '#292c2d', skin: '#bb815b', shirt: '#618348', accent: '#c5d899' },
};

/** Cosmetic limb animation; world coordinates remain authoritative. */
export function PixelResident({ id, walking = false, action }: { id: string; walking?: boolean; action?: string }) {
  const palette = palettes[id] ?? palettes.ethan;
  return <svg className={`pixel-person ${walking ? 'walking' : ''} ${action === 'gather' ? 'gathering' : ''}`}
    viewBox="0 0 16 25" aria-hidden="true" shapeRendering="crispEdges"
    style={{ '--shirt': palette.shirt, '--accent': palette.accent } as CSSProperties}>
    <ellipse cx="8" cy="24" rx="6" ry="1" fill="#203d2d" opacity=".25" />
    <g className="sprite-body">
      <path d="M4 2h8v2h2v7h-2v2H4v-2H2V4h2z" fill="#382b29" />
      <path d="M4 4h8v6h-1v2H5v-2H4z" fill={palette.skin} />
      <path d="M4 2h8v2h2v3h-3V5H6v2H3V4h1z" fill={palette.hair} />
      <path d="M4 3h3v1H4z" fill="#fff0c4" opacity=".22" />
      <g className="sprite-eyes"><path d="M5 8h2v2H5zm5 0h2v2h-2z" fill="#29272c" /></g>
      <path d="M7 11h3v1H7z" fill="#985d49" />
      <path d="M5 13h7v7H4v-6h1z" fill={palette.shirt} />
      <path d="M6 13h4v2H6zM4 18h8v1H4z" fill={palette.accent} />
      <g className="sprite-arm left"><path d="M2 14h2v5H2z" fill={palette.shirt} /><path d="M2 18h2v3H2z" fill={palette.skin} /></g>
      <g className="sprite-arm right"><path d="M12 14h2v5h-2z" fill={palette.shirt} /><path d="M12 18h2v3h-2z" fill={palette.skin} /></g>
      <g className="sprite-leg left"><path d="M4 20h3v3H4z" fill="#3b4859" /><path d="M3 23h4v1H3z" fill="#483329" /></g>
      <g className="sprite-leg right"><path d="M9 20h3v3H9z" fill="#3b4859" /><path d="M9 23h4v1H9z" fill="#483329" /></g>
    </g>
  </svg>;
}
