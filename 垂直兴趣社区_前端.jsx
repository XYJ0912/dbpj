import { useState, useEffect, useCallback, createContext, useContext } from "react";

// ═══════════════════════════════════════════════════
// 配置 & Context
// ═══════════════════════════════════════════════════
const API = "http://127.0.0.1:5000/api";

const AuthContext = createContext(null);
function useAuth() { return useContext(AuthContext); }

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("vc_user")); } catch { return null; }
  });
  const login = (u) => { setUser(u); localStorage.setItem("vc_user", JSON.stringify(u)); };
  const logout = () => { setUser(null); localStorage.removeItem("vc_user"); };
  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

// ═══════════════════════════════════════════════════
// API 工具
// ═══════════════════════════════════════════════════
async function api(path, opts = {}) {
  const token = (() => { try { return JSON.parse(localStorage.getItem("vc_user"))?.token; } catch { return null; } })();
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  try {
    const res = await fetch(`${API}${path}`, { ...opts, headers: { ...headers, ...opts.headers } });
    const data = await res.json();
    return data;
  } catch (e) {
    return { code: -1, msg: "网络错误：请确认后端服务已启动在 " + API };
  }
}

// ═══════════════════════════════════════════════════
// 通用组件
// ═══════════════════════════════════════════════════
const colors = {
  bg: "#0f0f13", card: "#1a1a24", cardHover: "#22223a", border: "#2a2a3d",
  accent: "#7c5bf5", accentDim: "#5a3fd4", accentGlow: "rgba(124,91,245,0.15)",
  pink: "#e84393", cyan: "#00cec9", green: "#00b894", yellow: "#fdcb6e", orange: "#e17055",
  text: "#e8e8ef", textDim: "#8888a0", textMuted: "#555570",
};

function Badge({ children, color = colors.accent, style }) {
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: 20,
      background: color + "22", color, fontSize: 12, fontWeight: 600, ...style,
    }}>{children}</span>
  );
}

function Stat({ label, value, color = colors.text }) {
  return (
    <div style={{ textAlign: "center", minWidth: 60 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value ?? 0}</div>
      <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 2 }}>{label}</div>
    </div>
  );
}

function Card({ children, style, onClick, hover = true }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered && hover ? colors.cardHover : colors.card,
        border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20,
        transition: "all 0.2s", cursor: onClick ? "pointer" : "default", ...style,
      }}
    >{children}</div>
  );
}

function Button({ children, onClick, variant = "primary", style, disabled }) {
  const base = { border: "none", borderRadius: 10, padding: "10px 22px", fontSize: 14, fontWeight: 600, cursor: "pointer", transition: "all 0.2s", opacity: disabled ? 0.5 : 1 };
  const variants = {
    primary: { background: colors.accent, color: "#fff" },
    ghost: { background: "transparent", color: colors.accent, border: `1px solid ${colors.accent}33` },
    danger: { background: colors.pink + "22", color: colors.pink },
    success: { background: colors.green + "22", color: colors.green },
  };
  return <button onClick={onClick} disabled={disabled} style={{ ...base, ...variants[variant], ...style }}>{children}</button>;
}

function Input({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: "block", fontSize: 13, color: colors.textDim, marginBottom: 5 }}>{label}</label>}
      <input {...props} style={{
        width: "100%", boxSizing: "border-box", padding: "10px 14px", borderRadius: 10,
        border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
        fontSize: 14, outline: "none", ...props.style,
      }} />
    </div>
  );
}

function TextArea({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: "block", fontSize: 13, color: colors.textDim, marginBottom: 5 }}>{label}</label>}
      <textarea {...props} style={{
        width: "100%", boxSizing: "border-box", padding: "10px 14px", borderRadius: 10,
        border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
        fontSize: 14, outline: "none", resize: "vertical", minHeight: 100, ...props.style,
      }} />
    </div>
  );
}

function Toast({ msg, type = "success" }) {
  if (!msg) return null;
  const bg = type === "error" ? colors.pink : colors.green;
  return (
    <div style={{
      position: "fixed", top: 20, left: "50%", transform: "translateX(-50%)", zIndex: 9999,
      background: bg + "dd", color: "#fff", padding: "10px 28px", borderRadius: 12,
      fontSize: 14, fontWeight: 600, backdropFilter: "blur(10px)",
    }}>{msg}</div>
  );
}

function Loading() {
  return <div style={{ textAlign: "center", padding: 40, color: colors.textMuted }}>加载中...</div>;
}

function Empty({ text = "暂无数据" }) {
  return <div style={{ textAlign: "center", padding: 40, color: colors.textMuted }}>{text}</div>;
}

function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 4, background: colors.card, borderRadius: 12, padding: 4, marginBottom: 20 }}>
      {tabs.map(t => (
        <button key={t.key} onClick={() => onChange(t.key)} style={{
          flex: 1, padding: "10px 6px", border: "none", borderRadius: 10, cursor: "pointer",
          fontSize: 13, fontWeight: 600, transition: "all 0.2s",
          background: active === t.key ? colors.accent : "transparent",
          color: active === t.key ? "#fff" : colors.textDim,
        }}>{t.label}</button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：首页（热门内容）
// ═══════════════════════════════════════════════════
function HomePage({ onNavigate }) {
  const [tab, setTab] = useState("hot");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const paths = { hot: "/content/hot", liked: "/content/top-liked", fav: "/content/top-favorited" };
    api(paths[tab]).then(r => { setItems(r.data?.items || r.data || []); setLoading(false); });
  }, [tab]);

  const typeIcons = { text: "📝", image_post: "🎨", video_post: "🎬", mixed: "📦" };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ color: colors.text, margin: 0, fontSize: 28 }}>探索社区</h2>
        <p style={{ color: colors.textDim, margin: "6px 0 0", fontSize: 14 }}>发现二次元世界的精彩内容</p>
      </div>
      <TabBar
        tabs={[{ key: "hot", label: "🔥 综合热门" }, { key: "liked", label: "❤️ 最多点赞" }, { key: "fav", label: "⭐ 最多收藏" }]}
        active={tab} onChange={setTab}
      />
      {loading ? <Loading /> : items.length === 0 ? <Empty /> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((item, i) => (
            <Card key={item.content_id} onClick={() => onNavigate("content", item.content_id)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    {tab === "hot" && i < 3 && <span style={{ fontSize: 18 }}>{["🥇","🥈","🥉"][i]}</span>}
                    <span style={{ fontSize: 12, color: colors.textMuted }}>{typeIcons[item.content_type] || "📄"}</span>
                    <h3 style={{ margin: 0, color: colors.text, fontSize: 16, fontWeight: 600 }}>{item.title}</h3>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 13, color: colors.textDim }}>
                    <span onClick={e => { e.stopPropagation(); onNavigate("profile", item.author_id); }}
                      style={{ color: colors.accent, cursor: "pointer" }}>@{item.author_name}</span>
                    <span>{item.created_at?.slice(0, 10)}</span>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                  <Stat label="赞" value={item.like_count} color={colors.pink} />
                  <Stat label="评论" value={item.comment_count} color={colors.cyan} />
                  <Stat label="浏览" value={item.view_count} color={colors.textDim} />
                  {tab === "hot" && item.hot_score && <Stat label="热度" value={item.hot_score} color={colors.yellow} />}
                  {tab === "fav" && <Stat label="收藏" value={item.favorite_count} color={colors.yellow} />}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：内容详情
// ═══════════════════════════════════════════════════
function ContentPage({ contentId, onNavigate }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    Promise.all([
      api(`/content/${contentId}`),
      api(`/content/${contentId}/comments`),
    ]).then(([c, cm]) => {
      setData(c.data); setComments(cm.data || []); setLoading(false);
    });
  }, [contentId]);

  useEffect(() => { load(); }, [load]);

  const showToast = (msg, type) => { setToast({ msg, type }); setTimeout(() => setToast(null), 2000); };

  const doLike = () => api(`/content/${contentId}/like`, { method: "POST" }).then(r => {
    showToast(r.msg, r.code === 0 ? "success" : "error"); if (r.code === 0) load();
  });
  const doFav = () => api(`/content/${contentId}/favorite`, { method: "POST" }).then(r => {
    showToast(r.msg, r.code === 0 ? "success" : "error");
  });
  const doComment = () => {
    if (!newComment.trim()) return;
    api(`/content/${contentId}/comment`, { method: "POST", body: JSON.stringify({ text: newComment }) })
      .then(r => { showToast(r.msg, r.code === 0 ? "success" : "error"); if (r.code === 0) { setNewComment(""); load(); } });
  };

  // 记录浏览
  useEffect(() => { if (contentId) api(`/content/${contentId}/browse`, { method: "POST", body: JSON.stringify({}) }); }, [contentId]);

  if (loading) return <Loading />;
  if (!data) return <Empty text="内容不存在" />;

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} />}
      <Card hover={false} style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <Badge>{data.content_type}</Badge>
          <Badge color={colors.green}>{data.visibility}</Badge>
        </div>
        <h2 style={{ color: colors.text, margin: "0 0 10px", fontSize: 24 }}>{data.title}</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18, fontSize: 13, color: colors.textDim }}>
          <span onClick={() => onNavigate("profile", data.author_id)} style={{ color: colors.accent, cursor: "pointer", fontWeight: 600 }}>
            @{data.author_name}
          </span>
          <span>{data.created_at}</span>
        </div>
        <div style={{ color: colors.text, lineHeight: 1.8, fontSize: 15, marginBottom: 20, whiteSpace: "pre-wrap" }}>{data.body}</div>

        {/* 标签 / 作品 / 角色 */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {data.tags && data.tags.split(", ").map(t => <Badge key={t} color={colors.cyan}>#{t}</Badge>)}
          {data.works && data.works.split(", ").map(w => <Badge key={w} color={colors.orange}>📖 {w}</Badge>)}
          {data.characters && data.characters.split(", ").map(c => <Badge key={c} color={colors.pink}>👤 {c}</Badge>)}
        </div>

        {/* 统计 + 操作 */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: `1px solid ${colors.border}`, paddingTop: 16 }}>
          <div style={{ display: "flex", gap: 24 }}>
            <Stat label="赞" value={data.like_count} color={colors.pink} />
            <Stat label="评论" value={data.comment_count} color={colors.cyan} />
            <Stat label="浏览" value={data.view_count} color={colors.textDim} />
            {data.media_count > 0 && <Stat label="附件" value={data.media_count} color={colors.yellow} />}
          </div>
          {user && (
            <div style={{ display: "flex", gap: 8 }}>
              <Button onClick={doLike} variant="ghost" style={{ fontSize: 13 }}>❤️ 点赞</Button>
              <Button onClick={doFav} variant="ghost" style={{ fontSize: 13 }}>⭐ 收藏</Button>
            </div>
          )}
        </div>
      </Card>

      {/* 评论区 */}
      <h3 style={{ color: colors.text, marginBottom: 12 }}>评论 ({comments.length})</h3>
      {user && (
        <Card hover={false} style={{ marginBottom: 16 }}>
          <TextArea placeholder="写下你的评论..." value={newComment} onChange={e => setNewComment(e.target.value)} />
          <div style={{ textAlign: "right" }}><Button onClick={doComment}>发表评论</Button></div>
        </Card>
      )}
      {comments.length === 0 ? <Empty text="暂无评论" /> : comments.map(c => (
        <Card key={c.comment_id} hover={false} style={{ marginBottom: 8, padding: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ color: colors.accent, fontSize: 13, fontWeight: 600, cursor: "pointer" }}
              onClick={() => onNavigate("profile", c.author_id)}>@{c.author_name}</span>
            <span style={{ fontSize: 12, color: colors.textMuted }}>{c.created_at}</span>
          </div>
          {c.parent_comment_id && <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4 }}>↪ 回复 #{c.parent_comment_id}</div>}
          <div style={{ color: colors.text, fontSize: 14, lineHeight: 1.6 }}>{c.comment_text}</div>
        </Card>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：用户资料
// ═══════════════════════════════════════════════════
function ProfilePage({ userId, onNavigate }) {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [tab, setTab] = useState("tags");
  const [tabData, setTabData] = useState([]);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api(`/user/${userId}/profile`).then(r => { setProfile(r.data); setLoading(false); });
  }, [userId]);

  useEffect(() => {
    const paths = { tags: `/user/${userId}/tags?limit=10`, works: `/user/${userId}/works?limit=10`, friends: `/user/${userId}/friends`, feed: `/user/${userId}/feed` };
    api(paths[tab]).then(r => setTabData(r.data?.items || r.data || []));
  }, [userId, tab]);

  const doFollow = () => {
    api(`/follow/${userId}`, { method: "POST" }).then(r => {
      setToast({ msg: r.msg, type: r.code === 0 ? "success" : "error" });
      setTimeout(() => setToast(null), 2000);
    });
  };

  if (loading) return <Loading />;
  if (!profile) return <Empty text="用户不存在" />;

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} />}
      <Card hover={false} style={{ marginBottom: 20, textAlign: "center", padding: 30 }}>
        <div style={{
          width: 72, height: 72, borderRadius: "50%", margin: "0 auto 12px",
          background: `linear-gradient(135deg, ${colors.accent}, ${colors.pink})`,
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, color: "#fff",
        }}>{profile.username?.[0]?.toUpperCase()}</div>
        <h2 style={{ color: colors.text, margin: "0 0 4px", fontSize: 22 }}>{profile.username}</h2>
        {profile.bio && <p style={{ color: colors.textDim, margin: "0 0 8px", fontSize: 14 }}>{profile.bio}</p>}
        <div style={{ display: "flex", gap: 6, justifyContent: "center", marginBottom: 16 }}>
          {profile.roles && profile.roles.split(", ").map(r => <Badge key={r} color={r === "admin" ? colors.pink : colors.green}>{r}</Badge>)}
          <Badge color={colors.textMuted}>{profile.account_status}</Badge>
        </div>
        <div style={{ display: "flex", justifyContent: "center", gap: 32, marginBottom: 16 }}>
          <Stat label="内容" value={profile.content_count} color={colors.accent} />
          <Stat label="粉丝" value={profile.follower_count} color={colors.pink} />
          <Stat label="关注" value={profile.following_count} color={colors.cyan} />
        </div>
        {user && user.user_id !== userId && <Button onClick={doFollow}>+ 关注</Button>}
      </Card>

      <TabBar
        tabs={[
          { key: "tags", label: "🏷️ 标签偏好" }, { key: "works", label: "📖 作品偏好" },
          { key: "friends", label: "🤝 互关好友" }, { key: "feed", label: "📰 Feed" },
        ]}
        active={tab} onChange={setTab}
      />

      {tabData.length === 0 ? <Empty /> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {tab === "tags" && tabData.map((t, i) => (
            <Card key={i} hover={false} style={{ padding: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div><Badge color={colors.cyan}>#{t.tag_name}</Badge> <span style={{ fontSize: 12, color: colors.textMuted, marginLeft: 8 }}>{t.tag_category}</span></div>
              <span style={{ color: colors.yellow, fontWeight: 700, fontSize: 16 }}>{t.interaction_score}</span>
            </Card>
          ))}
          {tab === "works" && tabData.map((w, i) => (
            <Card key={i} hover={false} style={{ padding: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div><span style={{ color: colors.text, fontWeight: 600 }}>{w.work_name}</span> <Badge color={colors.orange}>{w.work_type}</Badge></div>
              <span style={{ color: colors.yellow, fontWeight: 700, fontSize: 16 }}>{w.interaction_score}</span>
            </Card>
          ))}
          {tab === "friends" && tabData.map((f, i) => (
            <Card key={i} onClick={() => onNavigate("profile", f.friend_id)} style={{ padding: 14 }}>
              <span style={{ color: colors.accent, fontWeight: 600 }}>@{f.friend_name}</span>
              <span style={{ fontSize: 12, color: colors.textMuted, marginLeft: 12 }}>互关于 {f.follow_time?.slice(0, 10)}</span>
            </Card>
          ))}
          {tab === "feed" && tabData.map(item => (
            <Card key={item.content_id} onClick={() => onNavigate("content", item.content_id)} style={{ padding: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                  <h4 style={{ margin: 0, color: colors.text, fontSize: 14 }}>{item.title}</h4>
                  <span style={{ fontSize: 12, color: colors.textDim }}>@{item.author_name} · {item.created_at?.slice(0, 10)}</span>
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                  <Stat label="赞" value={item.like_count} color={colors.pink} />
                  <Stat label="评" value={item.comment_count} color={colors.cyan} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：作品 & 角色
// ═══════════════════════════════════════════════════
function DiscoverPage({ onNavigate }) {
  const [tab, setTab] = useState("works");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api(tab === "works" ? "/works" : tab === "chars" ? "/characters" : "/tags")
      .then(r => { setItems(r.data?.items || r.data || []); setLoading(false); });
  }, [tab]);

  const workTypeColors = { anime: colors.pink, game: colors.cyan, novel: colors.yellow, manga: colors.orange, other: colors.textDim };

  return (
    <div>
      <h2 style={{ color: colors.text, margin: "0 0 6px", fontSize: 28 }}>发现</h2>
      <p style={{ color: colors.textDim, margin: "0 0 20px", fontSize: 14 }}>探索作品、角色和标签</p>
      <TabBar
        tabs={[{ key: "works", label: "📖 作品" }, { key: "chars", label: "👤 角色" }, { key: "tags", label: "🏷️ 标签" }]}
        active={tab} onChange={setTab}
      />
      {loading ? <Loading /> : items.length === 0 ? <Empty /> : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {tab === "works" && items.map(w => (
            <Card key={w.work_id} onClick={() => onNavigate("work", w.work_id)}>
              <h4 style={{ margin: "0 0 6px", color: colors.text }}>{w.work_name}</h4>
              <Badge color={workTypeColors[w.work_type]}>{w.work_type}</Badge>
              <div style={{ display: "flex", gap: 16, marginTop: 12 }}>
                <Stat label="内容" value={w.content_count} color={colors.accent} />
                <Stat label="总赞" value={w.total_likes} color={colors.pink} />
                <Stat label="总览" value={w.total_views} color={colors.textDim} />
              </div>
              {w.characters && <p style={{ fontSize: 12, color: colors.textMuted, marginTop: 8, marginBottom: 0 }}>角色: {w.characters}</p>}
            </Card>
          ))}
          {tab === "chars" && items.map(c => (
            <Card key={c.character_id}>
              <h4 style={{ margin: "0 0 6px", color: colors.text }}>{c.character_name}</h4>
              {c.works && <p style={{ fontSize: 12, color: colors.textMuted, margin: "0 0 10px" }}>{c.works}</p>}
              <div style={{ display: "flex", gap: 16 }}>
                <Stat label="内容" value={c.content_count} color={colors.accent} />
                <Stat label="总赞" value={c.total_likes} color={colors.pink} />
              </div>
            </Card>
          ))}
          {tab === "tags" && items.map(t => (
            <Card key={t.tag_id} onClick={() => onNavigate("tag", t.tag_name)} style={{ padding: 14 }}>
              <Badge color={colors.cyan} style={{ fontSize: 14 }}>#{t.tag_name}</Badge>
              {t.tag_category && <span style={{ fontSize: 12, color: colors.textMuted, marginLeft: 8 }}>{t.tag_category}</span>}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：按标签浏览
// ═══════════════════════════════════════════════════
function TagPage({ tagName, onNavigate }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api(`/content/by-tag?tag_name=${encodeURIComponent(tagName)}`).then(r => { setItems(r.data?.items || []); setLoading(false); });
  }, [tagName]);
  return (
    <div>
      <h2 style={{ color: colors.text, margin: "0 0 20px" }}><Badge color={colors.cyan} style={{ fontSize: 20 }}>#{tagName}</Badge></h2>
      {loading ? <Loading /> : items.length === 0 ? <Empty text="该标签下暂无内容" /> : items.map(item => (
        <Card key={item.content_id} onClick={() => onNavigate("content", item.content_id)} style={{ marginBottom: 10, padding: 14 }}>
          <h4 style={{ margin: "0 0 4px", color: colors.text }}>{item.title}</h4>
          <span style={{ fontSize: 12, color: colors.textDim }}>@{item.author_name} · ❤️ {item.like_count} · 💬 {item.comment_count}</span>
        </Card>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：发布内容
// ═══════════════════════════════════════════════════
function PublishPage({ onNavigate }) {
  const [form, setForm] = useState({ title: "", body: "", content_type: "text", visibility: "public", tag_ids: "", work_ids: "", character_ids: "" });
  const [toast, setToast] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {
    if (!form.title.trim()) { setToast({ msg: "标题不能为空", type: "error" }); setTimeout(() => setToast(null), 2000); return; }
    setSubmitting(true);
    const body = {
      ...form,
      tag_ids: form.tag_ids ? form.tag_ids.split(",").map(Number).filter(Boolean) : [],
      work_ids: form.work_ids ? form.work_ids.split(",").map(Number).filter(Boolean) : [],
      character_ids: form.character_ids ? form.character_ids.split(",").map(Number).filter(Boolean) : [],
    };
    api("/content", { method: "POST", body: JSON.stringify(body) }).then(r => {
      setSubmitting(false);
      if (r.code === 0) {
        setToast({ msg: "发布成功!", type: "success" });
        setTimeout(() => onNavigate("content", r.data.content_id), 1000);
      } else {
        setToast({ msg: r.msg, type: "error" });
      }
      setTimeout(() => setToast(null), 2000);
    });
  };

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} />}
      <h2 style={{ color: colors.text, margin: "0 0 20px", fontSize: 28 }}>发布内容</h2>
      <Card hover={false}>
        <Input label="标题 *" placeholder="请输入标题" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        <TextArea label="正文" placeholder="写下你的想法..." value={form.body} onChange={e => setForm({ ...form, body: e.target.value })} style={{ minHeight: 180 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <label style={{ fontSize: 13, color: colors.textDim }}>内容类型</label>
            <select value={form.content_type} onChange={e => setForm({ ...form, content_type: e.target.value })}
              style={{ width: "100%", padding: "10px 14px", borderRadius: 10, border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, marginTop: 5 }}>
              <option value="text">文字</option><option value="image_post">图片</option>
              <option value="video_post">视频</option><option value="mixed">混合</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, color: colors.textDim }}>可见性</label>
            <select value={form.visibility} onChange={e => setForm({ ...form, visibility: e.target.value })}
              style={{ width: "100%", padding: "10px 14px", borderRadius: 10, border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, marginTop: 5 }}>
              <option value="public">公开</option><option value="followers_only">仅关注</option><option value="private">私密</option>
            </select>
          </div>
        </div>
        <div style={{ marginTop: 14 }}>
          <Input label="标签 ID（逗号分隔，如 1,3,7）" placeholder="1,3" value={form.tag_ids} onChange={e => setForm({ ...form, tag_ids: e.target.value })} />
          <Input label="作品 ID（逗号分隔）" placeholder="4" value={form.work_ids} onChange={e => setForm({ ...form, work_ids: e.target.value })} />
          <Input label="角色 ID（逗号分隔）" placeholder="6,7" value={form.character_ids} onChange={e => setForm({ ...form, character_ids: e.target.value })} />
        </div>
        <div style={{ textAlign: "right", marginTop: 16 }}>
          <Button onClick={handleSubmit} disabled={submitting} style={{ padding: "12px 36px" }}>
            {submitting ? "发布中..." : "🚀 发布"}
          </Button>
        </div>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 页面：登录 / 注册
// ═══════════════════════════════════════════════════
function AuthPage({ onNavigate }) {
  const { login } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", bio: "" });
  const [toast, setToast] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {
    setSubmitting(true);
    const path = mode === "login" ? "/user/login" : "/user/register";
    const body = mode === "login" ? { username: form.username, password: form.password } : form;
    api(path, { method: "POST", body: JSON.stringify(body) }).then(r => {
      setSubmitting(false);
      if (r.code === 0) {
        login(r.data);
        setToast({ msg: r.msg, type: "success" });
        setTimeout(() => onNavigate("home"), 500);
      } else {
        setToast({ msg: r.msg, type: "error" });
      }
      setTimeout(() => setToast(null), 3000);
    });
  };

  return (
    <div style={{ maxWidth: 400, margin: "40px auto" }}>
      {toast && <Toast msg={toast.msg} type={toast.type} />}
      <Card hover={false} style={{ padding: 32 }}>
        <h2 style={{ color: colors.text, textAlign: "center", margin: "0 0 24px" }}>
          {mode === "login" ? "登录" : "注册"}
        </h2>
        <Input label="用户名" placeholder="请输入用户名" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
        {mode === "register" && <Input label="邮箱" placeholder="your@email.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />}
        <Input label="密码" type="password" placeholder="请输入密码" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
        {mode === "register" && <Input label="个人简介（可选）" placeholder="一句话介绍自己" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />}
        <Button onClick={handleSubmit} disabled={submitting} style={{ width: "100%", padding: 12, marginTop: 8 }}>
          {submitting ? "处理中..." : mode === "login" ? "登录" : "注册"}
        </Button>
        <p style={{ textAlign: "center", fontSize: 13, color: colors.textDim, marginTop: 16 }}>
          {mode === "login" ? "没有账号？" : "已有账号？"}
          <span onClick={() => setMode(mode === "login" ? "register" : "login")} style={{ color: colors.accent, cursor: "pointer", marginLeft: 4 }}>
            {mode === "login" ? "去注册" : "去登录"}
          </span>
        </p>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 主应用
// ═══════════════════════════════════════════════════
export default function App() {
  const [page, setPage] = useState({ name: "home", param: null });

  const navigate = useCallback((name, param = null) => {
    setPage({ name, param });
    window.scrollTo(0, 0);
  }, []);

  return (
    <AuthProvider>
      <div style={{ background: colors.bg, minHeight: "100vh", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
        <NavBar currentPage={page.name} onNavigate={navigate} />
        <main style={{ maxWidth: 860, margin: "0 auto", padding: "20px 16px 60px" }}>
          {page.name === "home" && <HomePage onNavigate={navigate} />}
          {page.name === "content" && <ContentPage contentId={page.param} onNavigate={navigate} />}
          {page.name === "profile" && <ProfilePage userId={page.param} onNavigate={navigate} />}
          {page.name === "discover" && <DiscoverPage onNavigate={navigate} />}
          {page.name === "tag" && <TagPage tagName={page.param} onNavigate={navigate} />}
          {page.name === "publish" && <PublishPage onNavigate={navigate} />}
          {page.name === "auth" && <AuthPage onNavigate={navigate} />}
        </main>
      </div>
    </AuthProvider>
  );
}

function NavBar({ currentPage, onNavigate }) {
  const { user, logout } = useAuth();
  const navItems = [
    { key: "home", label: "首页", icon: "🏠" },
    { key: "discover", label: "发现", icon: "🔍" },
  ];

  return (
    <nav style={{
      background: colors.card + "ee", borderBottom: `1px solid ${colors.border}`,
      backdropFilter: "blur(16px)", position: "sticky", top: 0, zIndex: 100,
    }}>
      <div style={{ maxWidth: 860, margin: "0 auto", padding: "0 16px", display: "flex", alignItems: "center", height: 56 }}>
        <div onClick={() => onNavigate("home")} style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 8, marginRight: 32 }}>
          <span style={{ fontSize: 22 }}>🌸</span>
          <span style={{ fontWeight: 800, fontSize: 17, color: colors.text }}>VertComm</span>
        </div>
        <div style={{ display: "flex", gap: 4, flex: 1 }}>
          {navItems.map(n => (
            <button key={n.key} onClick={() => onNavigate(n.key)} style={{
              background: currentPage === n.key ? colors.accentGlow : "transparent",
              color: currentPage === n.key ? colors.accent : colors.textDim,
              border: "none", borderRadius: 8, padding: "7px 14px", cursor: "pointer", fontSize: 13, fontWeight: 600,
            }}>{n.icon} {n.label}</button>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {user ? (
            <>
              <Button onClick={() => onNavigate("publish")} variant="primary" style={{ padding: "7px 16px", fontSize: 13 }}>✏️ 发布</Button>
              <button onClick={() => onNavigate("profile", user.user_id)} style={{
                background: `linear-gradient(135deg, ${colors.accent}, ${colors.pink})`,
                color: "#fff", border: "none", borderRadius: "50%", width: 34, height: 34,
                cursor: "pointer", fontWeight: 700, fontSize: 14,
              }}>{user.username?.[0]?.toUpperCase()}</button>
              <button onClick={() => { logout(); onNavigate("home"); }} style={{
                background: "transparent", border: "none", color: colors.textMuted, cursor: "pointer", fontSize: 12,
              }}>退出</button>
            </>
          ) : (
            <Button onClick={() => onNavigate("auth")} variant="ghost" style={{ padding: "7px 16px", fontSize: 13 }}>登录</Button>
          )}
        </div>
      </div>
    </nav>
  );
}
