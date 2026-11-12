import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileSearch,
  Fingerprint,
  FolderOpen,
  LayoutDashboard,
  Loader2,
  LockKeyhole,
  LogOut,
  Network,
  Scale,
  Search,
  ShieldCheck,
  Waves,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ApiError, refreshCsrf, apiCall } from "./api/client";
import type { User } from "./api/client";
import Workspace from "./Workspace";
import Message from "./components/Message";

const statusLabel: Record<string, string> = {
  Active: "调查中",
  Reviewing: "复核中",
  Submitted: "已结案",
};
function Logo() {
  return (
    <div className="brand">
      <span className="brand-icon">
        <Fingerprint size={25} />
      </span>
      <span>
        EchoCase<small>EVIDENCE → INSIGHT</small>
      </span>
    </div>
  );
}

export default function App() {
  const cache = useQueryClient();
  const user = useQuery({
    queryKey: ["me"],
    queryFn: () => apiCall((client) => client.getCurrentUser()),
    retry: false,
  });
  const [id, setId] = useState<string | null>(
    new URLSearchParams(location.search).get("case"),
  );
  useEffect(() => {
    const back = () => setId(new URLSearchParams(location.search).get("case"));
    addEventListener("popstate", back);
    return () => removeEventListener("popstate", back);
  }, []);
  const navigate = (next: string | null) => {
    history.pushState({}, "", next ? `?case=${next}` : location.pathname);
    setId(next);
  };
  if (user.isPending)
    return (
      <div className="boot">
        <Fingerprint size={44} />
        <p>正在打开调查工作台…</p>
      </div>
    );
  if (!user.data)
    return (
      <Login
        onLogin={(u) => {
          cache.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" });
          cache.setQueryData(["me"], u);
        }}
        error={
          user.error instanceof ApiError && user.error.status !== 401
            ? user.error
            : undefined
        }
      />
    );
  const logout = async () => {
    await apiCall((client) => client.logout());
    await refreshCsrf();
    cache.removeQueries({ predicate: (q) => q.queryKey[0] !== "me" });
    cache.setQueryData(["me"], null);
    navigate(null);
  };
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Logo />
        <div className="nav-label">工作空间</div>
        <button
          className={!id ? "nav-item active" : "nav-item"}
          onClick={() => navigate(null)}
        >
          <LayoutDashboard size={18} />
          案件总览
        </button>
        <div className={id ? "nav-item active" : "nav-item muted"}>
          <FolderOpen size={18} />
          调查工作台
        </div>
        <div className="sidebar-note">
          <ShieldCheck size={22} />
          <strong>让结论有据可循</strong>
          <p>
            查阅、关联、复核。
            <br />
            每一步判断，都留有来路。
          </p>
        </div>
        <div className="account">
          <span className="avatar">{user.data.email[0].toUpperCase()}</span>
          <div>
            <b>调查员</b>
            <small title={user.data.email}>{user.data.email}</small>
          </div>
          <button aria-label="退出登录" onClick={() => void logout()}>
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <span>工作空间</span>
            <ChevronRight size={14} />
            <b>{id ? "调查工作台" : "案件总览"}</b>
          </div>
          <span className="private-badge">
            <LockKeyhole size={13} />
            私人调查档案
          </span>
        </header>
        {id ? (
          <Workspace
            key={id}
            id={id}
            user={user.data}
            onBack={() => navigate(null)}
          />
        ) : (
          <Dashboard user={user.data} open={navigate} />
        )}
      </main>
    </div>
  );
}

function Login({
  onLogin,
  error: serviceError,
}: {
  onLogin: (u: User) => void;
  error?: unknown;
}) {
  const [register, setRegister] = useState(false),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [success, setSuccess] = useState("");
  const mutation = useMutation({
    mutationFn: async () => {
      if (register) {
        await apiCall((client) => client.register({ email, password }));
        setRegister(false);
        setSuccess("账户已创建。现在可以登录工作台。");
        return null;
      }
      const user = await apiCall((client) => client.login({ email, password }));
      await refreshCsrf();
      return user;
    },
    onSuccess: (u) => {
      if (u) onLogin(u);
    },
  });
  return (
    <div className="login">
      <section className="login-story">
        <Logo />
        <div>
          <span className="eyebrow">AN INVESTIGATION WORKSPACE</span>
          <h1>
            每一条结论，
            <br />
            都有证据可循。
          </h1>
          <p>
            在细节中发现线索，在关联中重建事实。
            <br />
            从第一份档案，到一份有根据的结论。
          </p>
          <div className="story-diagram">
            <span>
              <FileSearch />
              发现
            </span>
            <i />
            <span>
              <Network />
              关联
            </span>
            <i />
            <span>
              <Scale />
              判断
            </span>
          </div>
        </div>
        <small>EchoCase · 虚构案件，真实的调查过程</small>
      </section>
      <section className="login-form">
        <div className="login-card">
          <span className="eyebrow">YOUR NEXT INVESTIGATION</span>
          <h2>{register ? "创建调查员账户" : "欢迎回到工作台"}</h2>
          <p className="subtle">
            {register
              ? "调查档案仅对你本人可见。"
              : "登录后，继续你尚未完成的调查。"}
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setSuccess("");
              mutation.mutate();
            }}
          >
            <label>
              邮箱
              <Input
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@example.com"
              />
            </label>
            <label>
              密码
              <Input
                type="password"
                required
                minLength={12}
                autoComplete={register ? "new-password" : "current-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="至少 12 位，含大小写字母与数字"
              />
            </label>
            <Message error={mutation.error || serviceError} />
            {success && (
              <p role="status" className="notice success">
                {success}
              </p>
            )}
            <Button
              type="submit"
              className="full"
              size="lg"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? <Loader2 className="spin" /> : null}
              {register ? "创建账户" : "进入工作台"}
              <ArrowRight size={17} />
            </Button>
          </form>
          <p className="switch-auth">
            {register ? "已有账户？" : "第一次来到这里？"}
            <button
              onClick={() => {
                setRegister(!register);
                mutation.reset();
              }}
            >
              {register ? "登录" : "创建账户"}
            </button>
          </p>
          <div className="login-trust">
            <ShieldCheck size={16} />
            个人档案 · 安全保存 · 随时继续
          </div>
        </div>
      </section>
    </div>
  );
}

function Dashboard({ user, open }: { user: User; open: (id: string) => void }) {
  const cache = useQueryClient();
  const cases = useQuery({
    queryKey: ["cases", user.id],
    queryFn: () => apiCall((client) => client.getCases()),
  });
  const sessions = useQuery({
    queryKey: ["sessions", user.id],
    queryFn: () => apiCall((client) => client.listInvestigations()),
  });
  const start = useMutation({
    mutationFn: (caseId: string) =>
      apiCall((client) => client.startInvestigation({ caseId }), {
        key: crypto.randomUUID(),
      }),
    onSuccess: (s) => {
      void cache.invalidateQueries({ queryKey: ["sessions"] });
      open(s.id);
    },
  });
  const list = sessions.data ?? [];
  return (
    <div className="page dashboard">
      <div className="page-title">
        <div>
          <span className="eyebrow">YOUR INVESTIGATION DESK</span>
          <h1>
            案件总览<span className="title-dot">.</span>
          </h1>
          <p>从线索出发，让事实慢慢浮现。</p>
        </div>
        <span className="desk-date">
          <span className="live-dot" />
          私人工作空间
        </span>
      </div>
      <div className="stats">
        {[
          [FolderOpen, "我的调查", list.length],
          [
            FileSearch,
            "进行中",
            list.filter((s) => s.status === "Active").length,
          ],
          [
            Scale,
            "待复核",
            list.filter((s) => s.status === "Reviewing").length,
          ],
          [
            CheckCircle2,
            "已结案",
            list.filter((s) => s.status === "Submitted").length,
          ],
        ].map(([Icon, label, count]) => {
          const I = Icon as typeof FolderOpen;
          return (
            <div className="stat" key={String(label)}>
              <I size={21} />
              <span>{String(label)}</span>
              <strong>{String(count)}</strong>
            </div>
          );
        })}
      </div>
      <Message error={cases.error || sessions.error || start.error} />
      <div className="section-title">
        <h2>可调查案件</h2>
        <span>从这里开启一份新档案</span>
      </div>
      {cases.data?.map((c) => (
        <article className="case-feature" key={c.id}>
          <div className="case-info">
            <Badge variant="outline">档案 EC-001</Badge>
            <span className="case-kind">证据链调查</span>
            <h2>{c.title}</h2>
            <span className="case-subtitle">THE HARBOR FILE</span>
            <p>{c.synopsis}</p>
            <div className="case-meta">
              <span>
                <FileSearch size={15} />
                {c.evidenceCount} 份证据
              </span>
              <span>
                <Network size={15} />
                多条关联路径
              </span>
              <span>
                <Scale size={15} />
                独立结论
              </span>
            </div>
            <Button
              disabled={start.isPending}
              onClick={() => start.mutate(c.id)}
            >
              开始新调查
              <ArrowRight size={16} />
            </Button>
          </div>
          <div className="harbor-art" aria-label="雾港案件示意插图">
            <div className="map-grid" />
            <div className="harbor-ring ring-one" />
            <div className="harbor-ring ring-two" />
            <div className="map-coordinate coord-one">02:17 / WEST GATE</div>
            <div className="map-coordinate coord-two">
              EC-001 · HARBOR DISTRICT
            </div>
            <div className="art-file">
              <FolderOpen size={58} strokeWidth={1} />
              <span>雾港档案</span>
              <small>CLASSIFIED · FICTIONAL CASE</small>
            </div>
            <div className="art-pin">
              <Search size={25} />
            </div>
            <div className="art-wave">
              <Waves size={64} strokeWidth={1} />
            </div>
          </div>
        </article>
      ))}
      <div className="section-title">
        <h2>继续调查</h2>
        <span>最近更新的 50 份个人档案</span>
      </div>
      {sessions.isPending ? (
        <p className="subtle">正在读取档案…</p>
      ) : !list.length ? (
        <div className="empty">
          <FolderOpen size={28} />
          <div>
            <strong>你的调查桌已准备就绪</strong>
            <p>开始上方案件，第一条线索正等待你。</p>
          </div>
        </div>
      ) : (
        <div className="session-list">
          {list.map((s) => (
            <button
              className="session-row"
              key={s.id}
              onClick={() => open(s.id)}
            >
              <span className="file-icon">
                <FolderOpen size={22} />
              </span>
              <div>
                <strong>{s.title}</strong>
                <small>
                  档案 {s.id.slice(0, 8).toUpperCase()} ·{" "}
                  {new Date(s.updatedAt).toLocaleString("zh-CN")}
                </small>
              </div>
              <span className={"status status-" + s.status}>
                {statusLabel[s.status]}
              </span>
              <span className="session-progress">
                {s.evidence.filter((e) => e.examined).length} /{" "}
                {s.evidence.length} 证据
              </span>
              <ChevronRight size={18} />
            </button>
          ))}
        </div>
      )}
      <footer className="page-footer">
        事实先于判断。证据先于结论。
        <span>EchoCase / Investigation Workspace</span>
      </footer>
    </div>
  );
}
