// components/Header.jsx
export default function Header() {
  return (
    <header className="header">
      <div className="logo">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="3.5" fill="#9FE1CB" />
          <path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2
                   M3.55 3.55l1.41 1.41M13.04 13.04l1.41 1.41
                   M3.55 14.45l1.41-1.41M13.04 4.96l1.41-1.41"
            stroke="#9FE1CB" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </div>
      <div className="header-text">
        <h1>Autonomous Research Assistant</h1>
        <p>Agentic search · iterative reflection · structured report</p>
      </div>
    </header>
  );
}
