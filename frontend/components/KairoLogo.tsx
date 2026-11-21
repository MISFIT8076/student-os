export default function KairoLogo({
  size = "md",
  showSubtitle = true,
}: {
  size?: "sm" | "md" | "lg";
  showSubtitle?: boolean;
}) {
  const iconSize = size === "lg" ? 44 : size === "sm" ? 28 : 36;
  const titleSize = size === "lg" ? "28px" : size === "sm" ? "18px" : "22px";

  return (
    <div className="kairo-brand-container">
      <div className="kairo-emblem-wrap">
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="kairo-emblem-svg"
        >
          <defs>
            <linearGradient id="goldAegis" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fde68a" />
              <stop offset="45%" stopColor="#d97706" />
              <stop offset="100%" stopColor="#92400e" />
            </linearGradient>
            <linearGradient id="aegeanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#2563eb" />
            </linearGradient>
            <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Outer Greek Ring / Astrolabe */}
          <circle
            cx="24"
            cy="24"
            r="21"
            stroke="url(#goldAegis)"
            strokeWidth="1.75"
            strokeDasharray="2 3"
            opacity="0.85"
          />

          {/* Inner Horizon Ring */}
          <circle
            cx="24"
            cy="24"
            r="16.5"
            stroke="url(#aegeanGlow)"
            strokeWidth="1.25"
            opacity="0.7"
          />

          {/* Central Kairos Hourglass / Winged Scales of Time */}
          <path
            d="M17 12H31L24 23L17 12Z"
            fill="url(#goldAegis)"
            opacity="0.9"
          />
          <path
            d="M17 36H31L24 25L17 36Z"
            fill="url(#goldAegis)"
            opacity="0.9"
          />

          {/* Supreme Center Spark — The Opportune Moment */}
          <circle
            cx="24"
            cy="24"
            r="3"
            fill="#ffffff"
            filter="url(#softGlow)"
          />

          {/* Greek Cardinal Pointers */}
          <path d="M24 3V6" stroke="url(#goldAegis)" strokeWidth="2" strokeLinecap="round" />
          <path d="M24 42V45" stroke="url(#goldAegis)" strokeWidth="2" strokeLinecap="round" />
          <path d="M3 24H6" stroke="url(#goldAegis)" strokeWidth="2" strokeLinecap="round" />
          <path d="M42 24H45" stroke="url(#goldAegis)" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>

      <div className="kairo-wordmark">
        <div className="kairo-title-row">
          <span className="kairo-title" style={{ fontSize: titleSize }}>
            KAIRO
          </span>
          <span className="kairo-greek-tag">καιρός</span>
        </div>
        {showSubtitle && (
          <span className="kairo-subtitle">
            The Opportune Moment · AI Coordination Layer
          </span>
        )}
      </div>
    </div>
  );
}
