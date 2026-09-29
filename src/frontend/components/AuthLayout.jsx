export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-header">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>

        <div className="auth-content">
          {children}
        </div>
      </section>
    </main>
  );
}