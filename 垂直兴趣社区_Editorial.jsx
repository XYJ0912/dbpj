import { useState, useEffect, useCallback, createContext, useContext, useRef } from "react";

/* 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?   鍨傜洿鍏磋叮绀惧尯 鈥?Editorial Magazine Frontend
   
   Design direction: Japanese editorial magazine
   Tone: Warm, refined, culturally rooted
   Typography: Instrument Serif (display) + DM Sans (body)
   Palette: Washi cream, vermillion accent, deep indigo
   鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?*/

const API = globalThis.__VC_API_BASE__ || "http://127.0.0.1:5000/api";

// 鈹€鈹€ Auth Context 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const AuthCtx = createContext(null);
const useAuth = () => useContext(AuthCtx);

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vc_user")); } catch { return null; }
  });
  useEffect(() => {
    if (!user?.token) return;
    let ignore = false;
    apiFetch("/user/me").then((r) => {
      if (ignore) return;
      if (r.code === 0 && r.data) {
        const merged = { ...user, ...r.data, token: user.token };
        setUser(merged);
        localStorage.setItem("vc_user", JSON.stringify(merged));
      } else if (r.code === 401) {
        setUser(null);
        localStorage.removeItem("vc_user");
      }
    });
    return () => { ignore = true; };
  }, [user?.token]);
  const login = (u) => { setUser(u); localStorage.setItem("vc_user", JSON.stringify(u)); };
  const logout = () => { setUser(null); localStorage.removeItem("vc_user"); };
  return <AuthCtx.Provider value={{ user, login, logout }}>{children}</AuthCtx.Provider>;
}

// 鈹€鈹€ API helper 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
async function apiFetch(path, opts = {}) {
  const tk = (() => { try { return JSON.parse(localStorage.getItem("vc_user"))?.token; } catch { return null; } })();
  const h = { "Content-Type": "application/json", ...(tk ? { Authorization: `Bearer ${tk}` } : {}) };
  try {
    const r = await fetch(`${API}${path}`, { ...opts, headers: { ...h, ...opts.headers } });
    return await r.json();
  } catch { return { code: -1, msg: "缃戠粶閿欒锛氳纭鍚庣鏈嶅姟宸插惎鍔? }; }
}

// 鈹€鈹€ Design tokens 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const T = {
  // Warm, tinted neutrals 鈥?NO pure black, NO pure white
  bg:        "#faf6f0",       // warm washi cream
  bgAlt:     "#f2ebe0",       // slightly deeper cream
  surface:   "#ffffff",       // card surface with warmth from shadow
  ink:       "#1c1917",       // warm near-black (stone-900)
  inkSoft:   "#57534e",       // stone-600
  inkMuted:  "#a8a29e",       // stone-400
  rule:      "#e7e0d6",       // warm divider
  
  // Accent palette 鈥?vermillion + indigo, NOT purple/cyan/neon
  vermillion: "#c1272d",      // Japanese 鏈辫壊
  indigo:     "#2d3a6e",      // deep traditional indigo
  sage:       "#6b7f5e",      // muted matcha green
  ochre:      "#bf8a30",      // warm gold
  blush:      "#d4a59a",      // soft warm pink

  // Typography
  serif:  "'Instrument Serif', 'Noto Serif JP', Georgia, serif",
  sans:   "'DM Sans', 'Noto Sans JP', -apple-system, sans-serif",
  mono:   "'JetBrains Mono', 'Fira Code', monospace",

  // Spacing (8px baseline grid)
  s1: 4, s2: 8, s3: 12, s4: 16, s5: 24, s6: 32, s7: 48, s8: 64, s9: 96,

  // Transitions 鈥?NO bounce, intentional easing
  ease: "cubic-bezier(0.22, 1, 0.36, 1)",
  dur: "0.3s",
};

// 鈹€鈹€ Inject fonts & global styles 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const fontLink = document.createElement("link");
fontLink.rel = "stylesheet";
fontLink.href = "https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Instrument+Serif:ital@0;1&family=Noto+Serif+JP:wght@400;700&display=swap";
if (!document.querySelector(`link[href="${fontLink.href}"]`)) document.head.appendChild(fontLink);

const globalId = "vc-editorial-global";
if (!document.getElementById(globalId)) {
  const style = document.createElement("style");
  style.id = globalId;
  style.textContent = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    ::selection { background: ${T.vermillion}22; color: ${T.ink}; }
    input, textarea, select, button { font-family: ${T.sans}; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .anim-up { animation: fadeUp 0.5s ${T.ease} both; }
    .anim-in { animation: fadeIn 0.4s ${T.ease} both; }
  `;
  document.head.appendChild(style);
}

// 鈹€鈹€ Primitives 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

function Rule({ spacing = T.s6 }) {
  return <div style={{ height: 1, background: T.rule, margin: `${spacing}px 0` }} />;
}

function Tag({ children, color = T.indigo, filled = false }) {
  return (
    <span style={{
      display: "inline-block", padding: "3px 10px", borderRadius: 3,
      fontSize: 11, fontFamily: T.sans, fontWeight: 500, letterSpacing: "0.04em",
      textTransform: "uppercase", lineHeight: 1.4, transition: `all ${T.dur} ${T.ease}`,
      background: filled ? color : "transparent",
      color: filled ? "#fff" : color,
      border: `1px solid ${filled ? color : color + "44"}`,
    }}>{children}</span>
  );
}

function Num({ value, label }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontFamily: T.serif, fontSize: 28, fontWeight: 400, color: T.ink, lineHeight: 1 }}>{value ?? 0}</div>
      <div style={{ fontSize: 10, fontFamily: T.sans, fontWeight: 500, color: T.inkMuted, letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function Btn({ children, onClick, variant = "primary", style: sx, disabled }) {
  const [hov, setHov] = useState(false);
  const styles = {
    primary: { bg: T.ink, bgH: T.indigo, color: "#faf6f0" },
    outline: { bg: "transparent", bgH: T.ink + "08", color: T.ink, border: `1px solid ${T.rule}` },
    accent:  { bg: T.vermillion, bgH: "#a52020", color: "#fff" },
  };
  const s = styles[variant];
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display: "inline-flex", alignItems: "center", gap: 8,
        padding: "10px 24px", borderRadius: 4, border: s.border || "none",
        background: hov && !disabled ? s.bgH : s.bg, color: s.color,
        fontSize: 13, fontWeight: 500, letterSpacing: "0.02em", cursor: disabled ? "default" : "pointer",
        transition: `all ${T.dur} ${T.ease}`, opacity: disabled ? 0.4 : 1, ...sx,
      }}>{children}</button>
  );
}

function Field({ label, ...props }) {
  return (
    <div style={{ marginBottom: T.s4 }}>
      {label && <label style={{ display: "block", fontSize: 11, fontFamily: T.sans, fontWeight: 500, color: T.inkSoft, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{label}</label>}
      <input {...props} style={{
        width: "100%", padding: "10px 14px", borderRadius: 4,
        border: `1px solid ${T.rule}`, background: T.bg, color: T.ink,
        fontSize: 14, fontFamily: T.sans, outline: "none",
        transition: `border ${T.dur} ${T.ease}`, ...props.style,
      }} onFocus={e => e.target.style.borderColor = T.indigo}
         onBlur={e => e.target.style.borderColor = T.rule} />
    </div>
  );
}

function TextBox({ label, ...props }) {
  return (
    <div style={{ marginBottom: T.s4 }}>
      {label && <label style={{ display: "block", fontSize: 11, fontFamily: T.sans, fontWeight: 500, color: T.inkSoft, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{label}</label>}
      <textarea {...props} style={{
        width: "100%", padding: "12px 14px", borderRadius: 4,
        border: `1px solid ${T.rule}`, background: T.bg, color: T.ink,
        fontSize: 14, fontFamily: T.sans, outline: "none", resize: "vertical", minHeight: 120,
        lineHeight: 1.7, transition: `border ${T.dur} ${T.ease}`, ...props.style,
      }} onFocus={e => e.target.style.borderColor = T.indigo}
         onBlur={e => e.target.style.borderColor = T.rule} />
    </div>
  );
}

function Toast({ msg, type }) {
  if (!msg) return null;
  return (
    <div className="anim-up" style={{
      position: "fixed", bottom: 32, left: "50%", transform: "translateX(-50%)", zIndex: 999,
      padding: "12px 28px", borderRadius: 4, fontSize: 14, fontFamily: T.sans, fontWeight: 500,
      background: type === "error" ? T.vermillion : T.indigo, color: "#fff",
      boxShadow: "0 8px 32px rgba(0,0,0,0.15)",
    }}>{msg}</div>
  );
}

function useToast() {
  const [t, setT] = useState(null);
  const show = (msg, type = "success") => { setT({ msg, type }); setTimeout(() => setT(null), 2500); };
  return [t, show];
}

// 鈹€鈹€ Section Label (editorial style) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
function SectionLabel({ children }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: T.s5 }}>
      <div style={{ width: 20, height: 1, background: T.vermillion }} />
      <span style={{ fontSize: 10, fontFamily: T.sans, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: T.vermillion }}>{children}</span>
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Navigation
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function Nav({ current, go }) {
  const { user, logout } = useAuth();
  const links = [
    { key: "home", label: "棣栭〉" },
    { key: "discover", label: "鍙戠幇" },
  ];

  return (
    <header style={{
      position: "sticky", top: 0, zIndex: 100, background: T.bg + "ee",
      backdropFilter: "blur(12px)", borderBottom: `1px solid ${T.rule}`,
    }}>
      <div style={{ maxWidth: 980, margin: "0 auto", padding: "0 24px", display: "flex", alignItems: "center", height: 56 }}>
        {/* Wordmark */}
        <div onClick={() => go("home")} style={{ cursor: "pointer", marginRight: 40, display: "flex", alignItems: "baseline", gap: 6 }}>
          <span style={{ fontFamily: T.serif, fontSize: 22, color: T.ink, fontStyle: "italic" }}>Vertical</span>
          <span style={{ fontSize: 9, fontFamily: T.sans, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase", color: T.inkMuted }}>Community</span>
        </div>

        {/* Links */}
        <nav style={{ display: "flex", gap: 4, flex: 1 }}>
          {links.map(l => (
            <button key={l.key} onClick={() => go(l.key)} style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "6px 14px", fontSize: 13, fontFamily: T.sans, fontWeight: 500,
              color: current === l.key ? T.ink : T.inkMuted,
              borderBottom: current === l.key ? `2px solid ${T.vermillion}` : "2px solid transparent",
              transition: `all ${T.dur} ${T.ease}`,
            }}>{l.label}</button>
          ))}
        </nav>

        {/* Right */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {user ? (
            <>
              <Btn onClick={() => go("publish")} variant="accent" style={{ padding: "7px 18px", fontSize: 12 }}>鏂板缓</Btn>
              <div onClick={() => go("profile", user.user_id)} style={{
                width: 32, height: 32, borderRadius: "50%", cursor: "pointer",
                background: T.indigo, display: "flex", alignItems: "center", justifyContent: "center",
                color: "#fff", fontFamily: T.sans, fontSize: 13, fontWeight: 600,
              }}>{user.username?.[0]?.toUpperCase()}</div>
              <button onClick={() => { logout(); go("home"); }} style={{
                background: "none", border: "none", fontSize: 11, color: T.inkMuted, cursor: "pointer",
                fontFamily: T.sans, letterSpacing: "0.04em",
              }}>閫€鍑?/button>
            </>
          ) : (
            <Btn onClick={() => go("auth")} variant="outline" style={{ padding: "7px 18px", fontSize: 12 }}>鐧诲綍</Btn>
          )}
        </div>
      </div>
    </header>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Home 鈥?Editorial magazine layout
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function HomePage({ go }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("hot");

  useEffect(() => {
    setLoading(true);
    const p = { hot: "/content/hot", liked: "/content/top-liked", fav: "/content/top-favorited" };
    apiFetch(p[tab]).then(r => { setItems(r.data?.items || r.data || []); setLoading(false); });
  }, [tab]);

  const typeLabel = { text: "鏂囩珷", image_post: "鍥鹃泦", video_post: "瑙嗛", mixed: "缁煎悎" };
  const hero = items[0];
  const rest = items.slice(1);

  return (
    <div className="anim-in">
      {/* Masthead */}
      <div style={{ textAlign: "center", padding: `${T.s8}px 0 ${T.s6}px` }}>
        <h1 style={{ fontFamily: T.serif, fontSize: "clamp(36px, 5vw, 56px)", fontWeight: 400, color: T.ink, lineHeight: 1.1, marginBottom: T.s3 }}>
          鎺㈢储绀惧尯
        </h1>
        <p style={{ fontFamily: T.sans, fontSize: 15, color: T.inkSoft, fontWeight: 300, maxWidth: 400, margin: "0 auto" }}>
          鍙戠幇浜屾鍏冧笘鐣岄噷鍊煎緱涓€璇荤殑鍐呭
        </p>
      </div>

      {/* Tab row */}
      <div style={{ display: "flex", justifyContent: "center", gap: T.s5, marginBottom: T.s7 }}>
        {[
          { key: "hot", label: "缁煎悎鐑棬" },
          { key: "liked", label: "鏈€鍙楀枩鐖? },
          { key: "fav", label: "绮鹃€夋敹钘? },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            background: "none", border: "none", cursor: "pointer",
            fontSize: 13, fontFamily: T.sans, fontWeight: tab === t.key ? 600 : 400,
            color: tab === t.key ? T.ink : T.inkMuted, paddingBottom: 4,
            borderBottom: tab === t.key ? `2px solid ${T.vermillion}` : "2px solid transparent",
            transition: `all ${T.dur} ${T.ease}`,
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? (
        <p style={{ textAlign: "center", color: T.inkMuted, fontFamily: T.sans, padding: T.s8 }}>杞藉叆涓€?/p>
      ) : items.length === 0 ? (
        <p style={{ textAlign: "center", color: T.inkMuted, fontFamily: T.sans, padding: T.s8 }}>鏆傛棤鍐呭</p>
      ) : (
        <>
          {/* Hero card 鈥?editorial feature */}
          {hero && (
            <div onClick={() => go("content", hero.content_id)} className="anim-up" style={{
              cursor: "pointer", marginBottom: T.s7, padding: `${T.s7}px ${T.s6}px`,
              background: T.surface, borderRadius: 2, position: "relative",
              boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 12px 48px rgba(0,0,0,0.06)",
              transition: `box-shadow ${T.dur} ${T.ease}`,
              display: "grid", gridTemplateColumns: "1fr auto", gap: T.s6, alignItems: "center",
            }}>
              <div>
                <div style={{ display: "flex", gap: 8, marginBottom: T.s4 }}>
                  <Tag color={T.vermillion} filled>{typeLabel[hero.content_type] || "鍐呭"}</Tag>
                  {tab === "hot" && hero.hot_score && <Tag color={T.ochre}>鐑害 {hero.hot_score}</Tag>}
                </div>
                <h2 style={{ fontFamily: T.serif, fontSize: "clamp(24px, 3vw, 34px)", fontWeight: 400, color: T.ink, lineHeight: 1.25, marginBottom: T.s3 }}>
                  {hero.title}
                </h2>
                <div style={{ display: "flex", alignItems: "center", gap: T.s4, fontFamily: T.sans, fontSize: 13, color: T.inkSoft }}>
                  <span onClick={e => { e.stopPropagation(); go("profile", hero.author_id); }}
                    style={{ fontWeight: 600, color: T.indigo, cursor: "pointer" }}>
                    {hero.author_name}
                  </span>
                  <span style={{ color: T.inkMuted }}>{hero.created_at?.slice(0, 10)}</span>
                </div>
              </div>
              <div style={{ display: "flex", gap: T.s6, paddingLeft: T.s6, borderLeft: `1px solid ${T.rule}` }}>
                <Num value={hero.like_count} label="璧? />
                <Num value={hero.comment_count} label="璇勮" />
                <Num value={hero.view_count} label="闃呰" />
              </div>
            </div>
          )}

          {/* Content list 鈥?clean editorial list */}
          <div style={{ display: "flex", flexDirection: "column" }}>
            {rest.map((item, i) => (
              <div key={item.content_id} className="anim-up" style={{ animationDelay: `${i * 0.04}s` }}>
                <div onClick={() => go("content", item.content_id)} style={{
                  cursor: "pointer", padding: `${T.s5}px 0`,
                  display: "grid", gridTemplateColumns: "40px 1fr auto", gap: T.s4, alignItems: "center",
                }}>
                  {/* Number */}
                  <span style={{ fontFamily: T.serif, fontSize: 28, color: i < 2 ? T.vermillion : T.inkMuted, fontStyle: "italic", textAlign: "right" }}>
                    {String(i + 2).padStart(2, "0")}
                  </span>

                  {/* Text */}
                  <div>
                    <h3 style={{ fontFamily: T.sans, fontSize: 15, fontWeight: 500, color: T.ink, lineHeight: 1.4, marginBottom: 4 }}>{item.title}</h3>
                    <div style={{ fontSize: 12, fontFamily: T.sans, color: T.inkMuted, display: "flex", gap: T.s3 }}>
                      <span onClick={e => { e.stopPropagation(); go("profile", item.author_id); }}
                        style={{ fontWeight: 500, color: T.inkSoft, cursor: "pointer" }}>{item.author_name}</span>
                      <span>{item.created_at?.slice(0, 10)}</span>
                      <Tag color={T.sage}>{typeLabel[item.content_type] || "鍐呭"}</Tag>
                    </div>
                  </div>

                  {/* Stats */}
                  <div style={{ display: "flex", gap: T.s5, fontSize: 12, fontFamily: T.mono, color: T.inkMuted }}>
                    <span>{item.like_count} 璧?/span>
                    <span>{item.comment_count} 璇?/span>
                  </div>
                </div>
                <div style={{ height: 1, background: T.rule }} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Content Detail
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function ContentPage({ id, go }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [comments, setComments] = useState([]);
  const [newCmt, setNewCmt] = useState("");
  const [toast, showToast] = useToast();
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    Promise.all([apiFetch(`/content/${id}`), apiFetch(`/content/${id}/comments`)])
      .then(([c, cm]) => { setData(c.data); setComments(cm.data || []); setLoading(false); });
  }, [id]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (id) apiFetch(`/content/${id}/browse`, { method: "POST", body: "{}" }); }, [id]);

  const act = (path, method = "POST") => apiFetch(path, { method }).then(r => {
    showToast(r.msg, r.code === 0 ? "success" : "error"); if (r.code === 0) load();
  });

  if (loading) return <p style={{ textAlign: "center", padding: T.s9, color: T.inkMuted, fontFamily: T.sans }}>杞藉叆涓€?/p>;
  if (!data) return <p style={{ textAlign: "center", padding: T.s9, color: T.inkMuted, fontFamily: T.sans }}>鍐呭涓嶅瓨鍦?/p>;

  return (
    <article className="anim-in" style={{ maxWidth: 680, margin: "0 auto" }}>
      <Toast {...toast} />

      {/* Metadata ribbon */}
      <div style={{ padding: `${T.s7}px 0 ${T.s5}px`, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        <Tag color={T.vermillion}>{data.content_type}</Tag>
        <Tag color={T.sage}>{data.visibility}</Tag>
        <span style={{ fontSize: 12, fontFamily: T.sans, color: T.inkMuted, marginLeft: "auto" }}>{data.created_at}</span>
      </div>

      {/* Title */}
      <h1 style={{ fontFamily: T.serif, fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 400, color: T.ink, lineHeight: 1.2, marginBottom: T.s4 }}>
        {data.title}
      </h1>

      {/* Author */}
      <div onClick={() => go("profile", data.author_id)} style={{
        cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 10,
        padding: `${T.s3}px 0`, marginBottom: T.s5,
      }}>
        <div style={{ width: 36, height: 36, borderRadius: "50%", background: T.indigo, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontFamily: T.sans, fontSize: 14, fontWeight: 600 }}>
          {data.author_name?.[0]?.toUpperCase()}
        </div>
        <div>
          <div style={{ fontFamily: T.sans, fontWeight: 600, fontSize: 14, color: T.ink }}>{data.author_name}</div>
          {data.author_bio && <div style={{ fontSize: 12, color: T.inkMuted, fontFamily: T.sans }}>{data.author_bio}</div>}
        </div>
      </div>

      <Rule />

      {/* Body */}
      <div style={{ fontFamily: T.sans, fontSize: 16, lineHeight: 1.85, color: T.ink, padding: `${T.s5}px 0`, whiteSpace: "pre-wrap", fontWeight: 300 }}>
        {data.body}
      </div>

      {/* Tags / Works / Characters */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: `${T.s4}px 0` }}>
        {data.tags?.split(", ").filter(Boolean).map(t => <Tag key={t} color={T.indigo}>#{t}</Tag>)}
        {data.works?.split(", ").filter(Boolean).map(w => <Tag key={w} color={T.ochre}>{w}</Tag>)}
        {data.characters?.split(", ").filter(Boolean).map(c => <Tag key={c} color={T.vermillion}>{c}</Tag>)}
      </div>

      <Rule />

      {/* Stats + Actions */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: `${T.s4}px 0` }}>
        <div style={{ display: "flex", gap: T.s7 }}>
          <Num value={data.like_count} label="璧? />
          <Num value={data.comment_count} label="璇勮" />
          <Num value={data.view_count} label="闃呰" />
          {data.media_count > 0 && <Num value={data.media_count} label="闄勪欢" />}
        </div>
        {user && (
          <div style={{ display: "flex", gap: 8 }}>
            <Btn onClick={() => act(`/content/${id}/like`)} variant="outline" style={{ fontSize: 12, padding: "7px 16px" }}>璧?/Btn>
            <Btn onClick={() => act(`/content/${id}/favorite`)} variant="outline" style={{ fontSize: 12, padding: "7px 16px" }}>鏀惰棌</Btn>
          </div>
        )}
      </div>

      <Rule spacing={T.s7} />

      {/* Comments */}
      <SectionLabel>璇勮 路 {comments.length}</SectionLabel>

      {user && (
        <div style={{ marginBottom: T.s6 }}>
          <TextBox placeholder="鍒嗕韩浣犵殑鎯虫硶鈥? value={newCmt} onChange={e => setNewCmt(e.target.value)} />
          <div style={{ textAlign: "right" }}>
            <Btn onClick={() => {
              if (!newCmt.trim()) return;
              apiFetch(`/content/${id}/comment`, { method: "POST", body: JSON.stringify({ text: newCmt }) })
                .then(r => { showToast(r.msg, r.code === 0 ? "success" : "error"); if (r.code === 0) { setNewCmt(""); load(); } });
            }}>鍙戣〃</Btn>
          </div>
        </div>
      )}

      {comments.length === 0 ? (
        <p style={{ color: T.inkMuted, fontFamily: T.sans, fontSize: 14, padding: `${T.s5}px 0` }}>灏氭棤璇勮锛屾垚涓虹涓€涓彂瑷€鐨勪汉</p>
      ) : comments.map(c => (
        <div key={c.comment_id} className="anim-up" style={{ padding: `${T.s4}px 0`, borderBottom: `1px solid ${T.rule}` }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span onClick={() => go("profile", c.author_id)} style={{ fontFamily: T.sans, fontSize: 13, fontWeight: 600, color: T.indigo, cursor: "pointer" }}>{c.author_name}</span>
            <span style={{ fontSize: 11, fontFamily: T.mono, color: T.inkMuted }}>{c.created_at?.slice(5, 16)}</span>
          </div>
          {c.parent_comment_id && <div style={{ fontSize: 11, color: T.inkMuted, fontFamily: T.sans, marginBottom: 4 }}>鍥炲 #{c.parent_comment_id}</div>}
          <p style={{ fontFamily: T.sans, fontSize: 14, lineHeight: 1.7, color: T.ink, fontWeight: 300 }}>{c.comment_text}</p>
        </div>
      ))}
    </article>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Profile
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function ProfilePage({ uid, go }) {
  const { user } = useAuth();
  const [p, setP] = useState(null);
  const [tab, setTab] = useState("tags");
  const [td, setTd] = useState([]);
  const [toast, showToast] = useToast();
  const canViewFeed = Boolean(user && (user.user_id === uid || user.roles?.includes("admin")));

  useEffect(() => { apiFetch(`/user/${uid}/profile`).then(r => setP(r.data)); }, [uid]);
  useEffect(() => {
    if (tab === "feed" && !canViewFeed) {
      setTd([]);
      return;
    }
    const m = { tags: `/user/${uid}/tags?limit=10`, works: `/user/${uid}/works?limit=10`, friends: `/user/${uid}/friends`, feed: `/user/${uid}/feed` };
    apiFetch(m[tab]).then(r => setTd(r.data?.items || r.data || []));
  }, [uid, tab, canViewFeed]);


  const profile = p || { roles: [], follower_count: 0, following_count: 0, username: "", bio: "" };
  const roleList = Array.isArray(profile.roles) ? profile.roles : String(profile.roles || "").split(",").map(s => s.trim()).filter(Boolean);
  const contentCount = profile.published_content_count ?? profile.content_count ?? 0;
  const tabs = [
    { key: "tags", label: "鏍囩鍋忓ソ" }, { key: "works", label: "浣滃搧鍋忓ソ" },
    { key: "friends", label: "浜掑叧濂藉弸" },
    ...(canViewFeed ? [{ key: "feed", label: "鍔ㄦ€? }] : []),
  ];
  useEffect(() => {
    if (!tabs.some(t => t.key === tab)) setTab("tags");
  }, [tab, tabs]);

  return (
    <div className="anim-in">
      <Toast {...toast} />

      {/* Profile header 鈥?asymmetric layout */}
      <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: T.s7, padding: `${T.s8}px 0 ${T.s6}px`, alignItems: "start" }}>
        {/* Left: Avatar + stats */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            width: 100, height: 100, borderRadius: "50%", margin: "0 auto 16px",
            background: `linear-gradient(145deg, ${T.indigo}, ${T.vermillion})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 36, fontFamily: T.serif, fontStyle: "italic", color: "#fff",
          }}>{profile.username?.[0]?.toUpperCase()}</div>
          <div style={{ display: "flex", justifyContent: "center", gap: T.s5 }}>
            <Num value={contentCount} label="鍐呭" />
            <Num value={profile.follower_count} label="绮変笣" />
            <Num value={profile.following_count} label="鍏虫敞" />
          </div>
        </div>

        {/* Right: Info */}
        <div>
          <h1 style={{ fontFamily: T.serif, fontSize: 36, fontWeight: 400, color: T.ink, marginBottom: T.s2 }}>{profile.username}</h1>
          {profile.bio && <p style={{ fontFamily: T.sans, fontSize: 15, color: T.inkSoft, lineHeight: 1.6, fontWeight: 300, marginBottom: T.s3 }}>{profile.bio}</p>}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: T.s4 }}>
            {roleList.map(r => <Tag key={r} color={r === "admin" ? T.vermillion : T.sage} filled>{r}</Tag>)}
          </div>
          {user && user.user_id !== uid && (
            <Btn onClick={() => apiFetch(`/follow/${uid}`, { method: "POST" }).then(r => showToast(r.msg, r.code === 0 ? "success" : "error"))} variant="primary" style={{ fontSize: 12 }}>鍏虫敞</Btn>
          )}
        </div>
      </div>

      <Rule />

      {/* Tabs */}
      <div style={{ display: "flex", gap: T.s5, marginBottom: T.s6, paddingTop: T.s2 }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            background: "none", border: "none", cursor: "pointer",
            fontSize: 13, fontFamily: T.sans, fontWeight: tab === t.key ? 600 : 400,
            color: tab === t.key ? T.ink : T.inkMuted, paddingBottom: 4,
            borderBottom: tab === t.key ? `2px solid ${T.vermillion}` : "2px solid transparent",
          }}>{t.label}</button>
        ))}
      </div>

      {td.length === 0 ? <p style={{ color: T.inkMuted, fontFamily: T.sans, padding: T.s5 }}>鏆傛棤鏁版嵁</p> : (
        <div>
          {tab === "tags" && td.map((t, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${T.s3}px 0`, borderBottom: `1px solid ${T.rule}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: T.s3 }}>
                <Tag color={T.indigo}>#{t.tag_name}</Tag>
                <span style={{ fontSize: 11, color: T.inkMuted, fontFamily: T.sans }}>{t.tag_category}</span>
              </div>
              <span style={{ fontFamily: T.serif, fontSize: 22, color: T.ochre, fontStyle: "italic" }}>{t.interaction_score}</span>
            </div>
          ))}
          {tab === "works" && td.map((w, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: `${T.s3}px 0`, borderBottom: `1px solid ${T.rule}` }}>
              <div><span style={{ fontFamily: T.sans, fontWeight: 500, color: T.ink, fontSize: 14 }}>{w.tag_name || w.work_name}</span> <Tag color={T.ochre}>{w.work_type || "work"}</Tag></div>
              <span style={{ fontFamily: T.serif, fontSize: 22, color: T.ochre, fontStyle: "italic" }}>{w.interaction_score}</span>
            </div>
          ))}
          {tab === "friends" && td.map((f, i) => (
            <div key={i} onClick={() => go("profile", f.friend_id)} style={{ cursor: "pointer", padding: `${T.s3}px 0`, borderBottom: `1px solid ${T.rule}`, display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontFamily: T.sans, fontWeight: 600, color: T.indigo, fontSize: 14 }}>{f.friend_name}</span>
              <span style={{ fontSize: 11, fontFamily: T.mono, color: T.inkMuted }}>{f.follow_time?.slice(0, 10)}</span>
            </div>
          ))}
          {tab === "feed" && td.map(it => (
            <div key={it.content_id} onClick={() => go("content", it.content_id)} style={{ cursor: "pointer", padding: `${T.s4}px 0`, borderBottom: `1px solid ${T.rule}` }}>
              <h4 style={{ fontFamily: T.sans, fontWeight: 500, fontSize: 14, color: T.ink, marginBottom: 4 }}>{it.title}</h4>
              <div style={{ fontSize: 12, fontFamily: T.sans, color: T.inkMuted, display: "flex", gap: T.s3 }}>
                <span style={{ fontWeight: 500, color: T.inkSoft }}>{it.author_name}</span>
                <span>{it.created_at?.slice(0, 10)}</span>
                <span>{it.like_count} 璧?/span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Discover
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function DiscoverPage({ go }) {
  const [tab, setTab] = useState("works");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch(tab === "works" ? "/works" : tab === "chars" ? "/characters" : "/tags")
      .then(r => { setItems(r.data?.items || r.data || []); setLoading(false); });
  }, [tab]);

  return (
    <div className="anim-in">
      <div style={{ padding: `${T.s8}px 0 ${T.s5}px`, textAlign: "center" }}>
        <h1 style={{ fontFamily: T.serif, fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 400, color: T.ink }}>鍙戠幇</h1>
        <p style={{ fontFamily: T.sans, fontSize: 14, color: T.inkSoft, fontWeight: 300, marginTop: T.s2 }}>鎺㈢储浣滃搧涓栫晫銆佽鑹茬兢鍍忎笌鏍囩鍥捐氨</p>
      </div>

      <div style={{ display: "flex", justifyContent: "center", gap: T.s5, marginBottom: T.s7 }}>
        {[{ key: "works", label: "浣滃搧" }, { key: "chars", label: "瑙掕壊" }, { key: "tags", label: "鏍囩" }].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            background: "none", border: "none", cursor: "pointer",
            fontSize: 13, fontFamily: T.sans, fontWeight: tab === t.key ? 600 : 400,
            color: tab === t.key ? T.ink : T.inkMuted, paddingBottom: 4,
            borderBottom: tab === t.key ? `2px solid ${T.vermillion}` : "2px solid transparent",
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? <p style={{ textAlign: "center", color: T.inkMuted, fontFamily: T.sans }}>杞藉叆涓€?/p> : (
        <div style={{ display: "grid", gridTemplateColumns: tab === "tags" ? "repeat(3, 1fr)" : "repeat(2, 1fr)", gap: T.s4 }}>
          {tab === "works" && items.map(w => (
            <div key={w.work_id} onClick={() => go("tag", w.work_name)} className="anim-up" style={{
              padding: T.s5, background: T.surface, borderRadius: 2, cursor: "pointer",
              border: `1px solid ${T.rule}`, transition: `border ${T.dur} ${T.ease}`,
            }}>
              <h3 style={{ fontFamily: T.serif, fontSize: 20, fontWeight: 400, color: T.ink, marginBottom: T.s2 }}>{w.work_name}</h3>
              <Tag color={T.ochre}>{w.work_type}</Tag>
              <div style={{ display: "flex", gap: T.s5, marginTop: T.s4 }}>
                <Num value={w.content_count} label="鍐呭" />
                <Num value={w.total_likes} label="鎬昏禐" />
              </div>
              <p style={{ fontSize: 11, color: T.inkMuted, fontFamily: T.sans, marginTop: T.s3 }}>瑙掕壊鏁?{w.character_count ?? 0}</p>
            </div>
          ))}
          {tab === "chars" && items.map(c => (
            <div key={c.character_id} className="anim-up" style={{
              padding: T.s5, background: T.surface, borderRadius: 2, border: `1px solid ${T.rule}`,
            }}>
              <h3 style={{ fontFamily: T.serif, fontSize: 20, fontWeight: 400, color: T.ink, marginBottom: T.s2 }}>{c.character_name}</h3>
              <p style={{ fontSize: 12, color: T.inkSoft, fontFamily: T.sans, marginBottom: T.s3 }}>鍏宠仈浣滃搧鏁?{c.work_count ?? 0}</p>
              <div style={{ display: "flex", gap: T.s5 }}>
                <Num value={c.content_count} label="鍐呭" />
                <Num value={c.total_likes} label="鎬昏禐" />
              </div>
            </div>
          ))}
          {tab === "tags" && items.map(t => (
            <div key={t.tag_id} onClick={() => go("tag", t.tag_name)} className="anim-up" style={{
              padding: `${T.s3}px ${T.s4}px`, cursor: "pointer",
              borderBottom: `1px solid ${T.rule}`, transition: `background ${T.dur} ${T.ease}`,
            }}>
              <Tag color={T.indigo}>#{t.tag_name}</Tag>
              {t.tag_category && <span style={{ fontSize: 11, color: T.inkMuted, fontFamily: T.sans, marginLeft: 8 }}>{t.tag_category}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Tag browse
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function TagPage({ name, go }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { apiFetch(`/content/by-tag?tag_name=${encodeURIComponent(name)}`).then(r => { setItems(r.data?.items || []); setLoading(false); }); }, [name]);

  return (
    <div className="anim-in">
      <div style={{ padding: `${T.s7}px 0 ${T.s5}px` }}>
        <SectionLabel>鏍囩</SectionLabel>
        <h1 style={{ fontFamily: T.serif, fontSize: 40, fontWeight: 400, color: T.ink }}>#{name}</h1>
      </div>
      <Rule />
      {loading ? <p style={{ color: T.inkMuted, fontFamily: T.sans, padding: T.s5 }}>杞藉叆涓€?/p> :
       items.length === 0 ? <p style={{ color: T.inkMuted, fontFamily: T.sans, padding: T.s5 }}>璇ユ爣绛句笅鏆傛棤鍐呭</p> :
       items.map(it => (
        <div key={it.content_id} onClick={() => go("content", it.content_id)} style={{ cursor: "pointer", padding: `${T.s4}px 0`, borderBottom: `1px solid ${T.rule}` }}>
          <h4 style={{ fontFamily: T.sans, fontSize: 15, fontWeight: 500, color: T.ink, marginBottom: 4 }}>{it.title}</h4>
          <div style={{ fontSize: 12, fontFamily: T.sans, color: T.inkMuted }}>{it.author_name} 路 {it.like_count} 璧?路 {it.comment_count} 璇勮</div>
        </div>
      ))}
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Publish
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function PublishPage({ go }) {
  const [form, setForm] = useState({ title: "", body: "", content_type: "text", visibility: "public", tag_ids: "", media_ids: "" });
  const [toast, showToast] = useToast();
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = () => {
    if (!form.title.trim()) return showToast("鏍囬涓嶈兘涓虹┖", "error");
    setBusy(true);
    const body = {
      ...form,
      tag_ids: form.tag_ids ? form.tag_ids.split(",").map(Number).filter(Boolean) : [],
      media_ids: form.media_ids ? form.media_ids.split(",").map(Number).filter(Boolean) : [],
    };
    apiFetch("/content", { method: "POST", body: JSON.stringify(body) }).then(r => {
      setBusy(false);
      if (r.code === 0) { showToast("鍙戝竷鎴愬姛"); setTimeout(() => go("content", r.data.content_id), 800); }
      else showToast(r.msg, "error");
    });
  };

  return (
    <div className="anim-in" style={{ maxWidth: 640, margin: "0 auto" }}>
      <Toast {...toast} />
      <div style={{ padding: `${T.s8}px 0 ${T.s5}px` }}>
        <SectionLabel>鍒涗綔</SectionLabel>
        <h1 style={{ fontFamily: T.serif, fontSize: 36, fontWeight: 400, color: T.ink }}>鍙戝竷鍐呭</h1>
      </div>
      <Rule />
      <div style={{ padding: `${T.s5}px 0` }}>
        <Field label="鏍囬" placeholder="涓轰綘鐨勫唴瀹硅捣涓€涓ソ鏍囬" value={form.title} onChange={e => set("title", e.target.value)} />
        <TextBox label="姝ｆ枃" placeholder="鍐欎笅浣犵殑鎯虫硶鈥? value={form.body} onChange={e => set("body", e.target.value)} style={{ minHeight: 200 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: T.s4 }}>
          <div>
            <label style={{ display: "block", fontSize: 11, fontFamily: T.sans, fontWeight: 500, color: T.inkSoft, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>绫诲瀷</label>
            <select value={form.content_type} onChange={e => set("content_type", e.target.value)} style={{ width: "100%", padding: "10px 14px", borderRadius: 4, border: `1px solid ${T.rule}`, background: T.bg, color: T.ink, fontSize: 14, fontFamily: T.sans }}>
              <option value="text">鏂囩珷</option><option value="image_post">鍥鹃泦</option><option value="video_post">瑙嗛</option><option value="mixed">缁煎悎</option>
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 11, fontFamily: T.sans, fontWeight: 500, color: T.inkSoft, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>鍙鎬?/label>
            <select value={form.visibility} onChange={e => set("visibility", e.target.value)} style={{ width: "100%", padding: "10px 14px", borderRadius: 4, border: `1px solid ${T.rule}`, background: T.bg, color: T.ink, fontSize: 14, fontFamily: T.sans }}>
              <option value="public">鍏紑</option><option value="followers_only">浠呭叧娉ㄨ€?/option><option value="private">绉佸瘑</option>
            </select>
          </div>
        </div>
        <div style={{ marginTop: T.s4 }}>
          <Field label="鏍囩 ID锛堢粺涓€鏍囩锛岄€楀彿鍒嗛殧锛? placeholder="濡?17,25,101,201" value={form.tag_ids} onChange={e => set("tag_ids", e.target.value)} />
          <Field label="濯掍綋 ID锛堝彲閫夛級" placeholder="濡?1,2" value={form.media_ids} onChange={e => set("media_ids", e.target.value)} />
        </div>
        <div style={{ textAlign: "right", paddingTop: T.s4 }}>
          <Btn onClick={submit} disabled={busy} variant="accent" style={{ padding: "12px 40px" }}>
            {busy ? "鍙戝竷涓€? : "鍙戝竷"}
          </Btn>
        </div>
      </div>
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// Auth
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?function AuthPage({ go }) {
  const { login } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", bio: "" });
  const [toast, showToast] = useToast();
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = () => {
    setBusy(true);
    const path = mode === "login" ? "/user/login" : "/user/register";
    const body = mode === "login" ? { username: form.username, password: form.password } : form;
    apiFetch(path, { method: "POST", body: JSON.stringify(body) }).then(r => {
      setBusy(false);
      if (r.code === 0) { login(r.data); showToast(r.msg); setTimeout(() => go("home"), 600); }
      else showToast(r.msg, "error");
    });
  };

  return (
    <div className="anim-in" style={{ maxWidth: 380, margin: `${T.s9}px auto 0` }}>
      <Toast {...toast} />
      <div style={{ textAlign: "center", marginBottom: T.s7 }}>
        <h1 style={{ fontFamily: T.serif, fontSize: 32, fontWeight: 400, color: T.ink }}>
          {mode === "login" ? "娆㈣繋鍥炴潵" : "鍔犲叆绀惧尯"}
        </h1>
      </div>
      <div style={{ padding: T.s5, background: T.surface, borderRadius: 2, border: `1px solid ${T.rule}` }}>
        <Field label="鐢ㄦ埛鍚? placeholder="浣犵殑鐢ㄦ埛鍚? value={form.username} onChange={e => set("username", e.target.value)} />
        {mode === "register" && <Field label="閭" placeholder="email@example.com" value={form.email} onChange={e => set("email", e.target.value)} />}
        <Field label="瀵嗙爜" type="password" placeholder="鑷冲皯 6 浣? value={form.password} onChange={e => set("password", e.target.value)} />
        {mode === "register" && <Field label="涓汉绠€浠? placeholder="涓€鍙ヨ瘽浠嬬粛鑷繁锛堝彲閫夛級" value={form.bio} onChange={e => set("bio", e.target.value)} />}
        <Btn onClick={submit} disabled={busy} variant="primary" style={{ width: "100%", justifyContent: "center", marginTop: T.s2 }}>
          {busy ? "澶勭悊涓€? : mode === "login" ? "鐧诲綍" : "娉ㄥ唽"}
        </Btn>
      </div>
      <p style={{ textAlign: "center", fontSize: 13, fontFamily: T.sans, color: T.inkMuted, marginTop: T.s4 }}>
        {mode === "login" ? "杩樻病鏈夎处鍙凤紵" : "宸叉湁璐﹀彿锛?}
        <span onClick={() => setMode(mode === "login" ? "register" : "login")}
          style={{ color: T.vermillion, cursor: "pointer", fontWeight: 500, marginLeft: 4 }}>
          {mode === "login" ? "娉ㄥ唽" : "鐧诲綍"}
        </span>
      </p>
    </div>
  );
}

// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?// App Shell
// 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?export default function App() {
  const [page, setPage] = useState({ n: "home", p: null });
  const go = useCallback((n, p = null) => { setPage({ n, p }); window.scrollTo({ top: 0, behavior: "smooth" }); }, []);

  return (
    <AuthProvider>
      <div style={{ background: T.bg, minHeight: "100vh", fontFamily: T.sans, color: T.ink }}>
        <Nav current={page.n} go={go} />
        <main style={{ maxWidth: 980, margin: "0 auto", padding: "0 24px 80px" }}>
          {page.n === "home" && <HomePage go={go} />}
          {page.n === "content" && <ContentPage id={page.p} go={go} />}
          {page.n === "profile" && <ProfilePage uid={page.p} go={go} />}
          {page.n === "discover" && <DiscoverPage go={go} />}
          {page.n === "tag" && <TagPage name={page.p} go={go} />}
          {page.n === "publish" && <PublishPage go={go} />}
          {page.n === "auth" && <AuthPage go={go} />}
        </main>

        {/* Footer */}
        <footer style={{ borderTop: `1px solid ${T.rule}`, padding: `${T.s6}px 24px`, textAlign: "center" }}>
          <span style={{ fontFamily: T.serif, fontSize: 14, fontStyle: "italic", color: T.inkMuted }}>Vertical</span>
          <span style={{ fontSize: 11, fontFamily: T.sans, color: T.inkMuted, marginLeft: 6 }}>Community 路 鍨傜洿鍏磋叮绀惧尯</span>
        </footer>
      </div>
    </AuthProvider>
  );
}


