/**
 * 藍玫瑰和籠子 — 簡潔解鎖動畫（≤2 秒）
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * 1. 藍玫瑰剪影淡入
 * 2. 線條籠子包圍（~1.2s）
 * 3. 微光閃爍後淡出 + 文字
 * 不做多餘功能
 */
import { useEffect } from "react";

interface Props {
  show: boolean;
  onDone: () => void;
}

export default function BlueRoseUnlockAnimation({ show, onDone }: Props) {
  useEffect(() => {
    if (!show) return;
    const t = window.setTimeout(onDone, 1900);
    return () => window.clearTimeout(t);
  }, [show, onDone]);

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80"
      style={{ pointerEvents: "all" }}
      aria-live="polite"
    >
      <style>{`
        @keyframes br-fade-in { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
        @keyframes br-cage { from { opacity: 0; transform: scale(1.15); } to { opacity: 1; transform: scale(1); } }
        @keyframes br-glow { 0%,100% { filter: drop-shadow(0 0 4px #5B8CFF); } 50% { filter: drop-shadow(0 0 18px #9EC5FF); } }
        @keyframes br-out { to { opacity: 0; } }
        .br-root { animation: br-fade-in 0.35s ease-out both, br-out 0.35s ease-in 1.55s both; }
        .br-cage { animation: br-cage 1.2s ease-out both, br-glow 0.35s ease-in-out 1.2s 1; }
      `}</style>
      <div className="br-root flex flex-col items-center gap-4 text-center">
        <svg width="140" height="160" viewBox="0 0 140 160" className="br-cage">
          {/* 籠子 */}
          <rect
            x="18"
            y="12"
            width="104"
            height="130"
            rx="8"
            fill="none"
            stroke="#9EC5FF"
            strokeWidth="2"
            opacity="0.85"
          />
          {[38, 58, 78, 98].map((x) => (
            <line
              key={x}
              x1={x}
              y1="18"
              x2={x}
              y2="136"
              stroke="#5B8CFF"
              strokeWidth="1.5"
              opacity="0.7"
            />
          ))}
          {/* 藍玫瑰剪影（簡約） */}
          <g transform="translate(70 78)">
            <ellipse cx="0" cy="0" rx="22" ry="16" fill="#3A6FE8" opacity="0.95" />
            <ellipse cx="-8" cy="-6" rx="14" ry="10" fill="#5B8CFF" opacity="0.9" />
            <ellipse cx="10" cy="-4" rx="12" ry="9" fill="#7AA8FF" opacity="0.85" />
            <circle cx="0" cy="2" r="6" fill="#1A2744" />
            <path
              d="M0 18 C -6 34, -14 42, -10 52"
              fill="none"
              stroke="#2A8F5A"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </g>
        </svg>
        <p className="text-sm font-semibold tracking-wide text-[#9EC5FF]">
          藍玫瑰和籠子 已解鎖
        </p>
      </div>
    </div>
  );
}
