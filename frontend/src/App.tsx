import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  FileSearch,
  Fingerprint,
  FolderOpen,
  GitBranch,
  LayoutDashboard,
  Loader2,
  LockKeyhole,
  LogOut,
  Network,
  RefreshCw,
  Scale,
  Search,
  ShieldCheck,
  StickyNote,
  Waves,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ApiError, refreshCsrf, request } from "./api/client";
import type { Case, Evidence, Session, User } from "./api/client";
import EvidenceGraph from "./EvidenceGraph";

const statusLabel: Record<string, string> = {
  Active: "调查中",
  Reviewing: "复核中",
  Submitted: "已结案",
};
function Message({ error }: { error: unknown }) {
  if (!error) return null;
  return (
    <div role="alert" className="notice error">
      <span>{error instanceof Error ? error.message : "操作未完成。"}</span>
      {error instanceof ApiError && error.traceId && (
        <small>追踪编号：{error.traceId}</small>
      )}
    </div>
  );
}
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
    queryFn: () => request<User>("/api/auth/me"),
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
    await request("/api/auth/logout", { method: "POST" });
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
        await request("/api/auth/register", {
          method: "POST",
          body: { email, password },
        });
        setRegister(false);
        setSuccess("账户已创建。现在可以登录工作台。");
        return null;
      }
      const user = await request<User>("/api/auth/login", {
        method: "POST",
        body: { email, password },
      });
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
    queryFn: () => request<Case[]>("/api/cases"),
  });
  const sessions = useQuery({
    queryKey: ["sessions", user.id],
    queryFn: () => request<Session[]>("/api/investigations"),
  });
  const start = useMutation({
    mutationFn: (caseId: string) =>
      request<Session>("/api/investigations", {
        method: "POST",
        body: { caseId },
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

type Operation = {
  route: string;
  body?: unknown;
  method?: string;
  version: number;
  key: string;
};
function Workspace({
  id,
  user,
  onBack,
}: {
  id: string;
  user: User;
  onBack: () => void;
}) {
  const cache = useQueryClient(),
    qk = ["session", user.id, id];
  const [tab, setTab] = useState("evidence"),
    [selected, setSelected] = useState<Evidence | null>(null),
    [notes, setNotes] = useState(""),
    [dirty, setDirty] = useState(false),
    [saved, setSaved] = useState(false);
  const query = useQuery({
    queryKey: qk,
    queryFn: () => request<Session>(`/api/investigations/${id}`),
    refetchInterval: 30_000,
  });
  useEffect(() => {
    if (query.data && !dirty) setNotes(query.data.notes);
  }, [query.data, dirty]);
  const mutation = useMutation({
    mutationFn: (op: Operation) =>
      request<Session>(`/api/investigations/${id}/${op.route}`, {
        ...op,
        method: op.method ?? "POST",
      }),
    onMutate: async (op) => {
      await cache.cancelQueries({ queryKey: qk });
      const previous = cache.getQueryData<Session>(qk);
      if (op.route === "notes" && previous)
        cache.setQueryData(qk, {
          ...previous,
          notes: (op.body as { notes: string }).notes,
        });
      return { previous };
    },
    onError: (_error, _op, context) => {
      if (context?.previous) cache.setQueryData(qk, context.previous);
    },
    onSuccess: (s, op) => {
      cache.setQueryData(qk, s);
      if (op.route === "notes") {
        setDirty(false);
        setSaved(true);
      }
    },
    onSettled: () => {
      void cache.invalidateQueries({ queryKey: qk });
      void cache.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
  const s = query.data;
  const act = (route: string, body?: unknown, method?: string) => {
    if (s)
      mutation.mutate({
        route,
        body,
        method,
        version: s.version,
        key: crypto.randomUUID(),
      });
  };
  if (query.isPending)
    return (
      <div className="page loading">
        <Loader2 className="spin" />
        正在读取调查档案…
      </div>
    );
  if (!s)
    return (
      <div className="page">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft />
          案件总览
        </Button>
        <Message error={query.error} />
        <Button onClick={() => void query.refetch()}>重新加载</Button>
      </div>
    );
  const examined = s.evidence.filter((e) => e.examined),
    editable = s.status === "Active",
    pending = mutation.isPending;
  const currentSelected = selected
    ? s.evidence.find((e) => e.id === selected.id)
    : null;
  return (
    <div className="page workspace">
      <button className="back-link" onClick={onBack}>
        <ArrowLeft size={15} />
        返回案件总览
      </button>
      <div className="workspace-title">
        <div>
          <span className="eyebrow">
            CASE EC-001 / {s.id.slice(0, 8).toUpperCase()}
          </span>
          <h1>
            {s.title}
            <span className={"status status-" + s.status}>
              {statusLabel[s.status]}
            </span>
          </h1>
          <p>所有判断，都从一条可核查的线索开始。</p>
        </div>
        <Button
          variant="outline"
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
        >
          <RefreshCw size={15} />
          刷新档案
        </Button>
      </div>
      <div className="investigation-strip">
        <div>
          <span className="strip-number">
            {String(examined.length).padStart(2, "0")}
            <small> / {String(s.evidence.length).padStart(2, "0")}</small>
          </span>
          <span>已调查证据</span>
        </div>
        <div className="strip-track">
          <span
            style={{ width: `${(examined.length / s.evidence.length) * 100}%` }}
          />
        </div>
        <div>
          <GitBranch size={19} />
          <b>{s.links.length}</b>
          <span>条证据关联</span>
        </div>
        <div className="version-label">档案版本 {s.version}</div>
      </div>
      <div className="tabs" role="tablist" aria-label="调查视图">
        {[
          [FileSearch, "evidence", "证据档案"],
          [Network, "graph", "关联图谱"],
          [StickyNote, "notes", "调查笔记"],
          [Scale, "verdict", "复核与结论"],
        ].map(([Icon, key, label]) => {
          const I = Icon as typeof FileSearch;
          return (
            <button
              role="tab"
              aria-selected={tab === key}
              key={String(key)}
              className={tab === key ? "tab active" : "tab"}
              onClick={() => {
                setTab(String(key));
                setSelected(null);
              }}
            >
              <I size={17} />
              {String(label)}
            </button>
          );
        })}
      </div>
      <Message error={mutation.error || query.error} />
      {mutation.error instanceof ApiError && mutation.error.status === 0 && (
        <Button
          variant="outline"
          disabled={pending}
          onClick={() =>
            mutation.variables && mutation.mutate(mutation.variables)
          }
        >
          重试同一次操作
        </Button>
      )}
      {tab === "evidence" && (
        <div className="evidence-layout">
          <section>
            <div className="section-title">
              <h2>
                证据档案<span className="count">{s.evidence.length}</span>
              </h2>
              <span>按线索逐步解锁</span>
            </div>
            <div className="evidence-grid">
              {s.evidence.map((e, index) => (
                <button
                  aria-label={`查看 ${e.title}`}
                  key={e.id}
                  onClick={() => setSelected(e)}
                  className={
                    "evidence-card " +
                    (e.locked ? "locked " : "") +
                    (currentSelected?.id === e.id ? "selected" : "")
                  }
                >
                  <div className="evidence-top">
                    <span className="evidence-index">
                      E-{String(index + 1).padStart(2, "0")}
                    </span>
                    {e.examined ? (
                      <CheckCircle2 size={18} className="verified" />
                    ) : e.locked ? (
                      <LockKeyhole size={17} />
                    ) : (
                      <Circle size={17} />
                    )}
                  </div>
                  <div className="evidence-glyph">
                    <FileSearch size={27} strokeWidth={1.5} />
                  </div>
                  <Badge variant="secondary">{e.kind}</Badge>
                  <h3>{e.title}</h3>
                  <p>{e.summary}</p>
                  <div className="evidence-bottom">
                    <span>
                      {e.examined ? "已调查" : e.locked ? "待解锁" : "待调查"}
                    </span>
                    <ArrowRight size={15} />
                  </div>
                </button>
              ))}
            </div>
          </section>
          <aside className="evidence-detail">
            {currentSelected ? (
              <>
                <div className="detail-head">
                  <span className="eyebrow">EVIDENCE DETAIL</span>
                  <button
                    aria-label="关闭证据详情"
                    onClick={() => setSelected(null)}
                  >
                    <X size={18} />
                  </button>
                </div>
                <Badge variant="outline">{currentSelected.kind}</Badge>
                <h2>{currentSelected.title}</h2>
                <p className="detail-summary">{currentSelected.summary}</p>
                {currentSelected.body ? (
                  <div className="evidence-body">
                    <span>
                      <Check size={15} />
                      调查记录
                    </span>
                    <p>{currentSelected.body}</p>
                  </div>
                ) : currentSelected.locked ? (
                  <div className="locked-message">
                    <LockKeyhole />
                    <p>
                      这条线索尚未解锁。
                      <br />
                      先完成已有线索的调查。
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="detail-divider" />
                    <p className="subtle">
                      打开证据后，完整内容会保存到你的调查档案中。
                    </p>
                    <Button
                      className="full"
                      disabled={!editable || pending}
                      onClick={() =>
                        act(`evidence/${currentSelected.id}/examine`)
                      }
                    >
                      <Search size={16} />
                      调查此证据
                    </Button>
                  </>
                )}
              </>
            ) : (
              <div className="detail-empty">
                <Search size={36} strokeWidth={1} />
                <h3>留意每一个细节</h3>
                <p>
                  选择一份证据，
                  <br />
                  查看详情并展开调查。
                </p>
                <span>SELECT AN EVIDENCE FILE</span>
              </div>
            )}
          </aside>
        </div>
      )}
      {tab === "graph" && (
        <section>
          <div className="section-title">
            <h2>让线索彼此连接</h2>
            <span>拖动节点调整布局；连接端点建立关联</span>
          </div>
          <EvidenceGraph
            session={s}
            disabled={!editable || pending}
            onLink={(sourceId, targetId, kind) =>
              act("links", { sourceId, targetId, kind })
            }
            onRemove={(linkId) => act(`links/${linkId}`, undefined, "DELETE")}
          />
        </section>
      )}
      {tab === "notes" && (
        <section className="writing-panel">
          <div className="section-title">
            <div>
              <span className="eyebrow">FIELD NOTES</span>
              <h2>记录观察，保留推理</h2>
            </div>
            <BookOpen size={25} />
          </div>
          <p className="subtle">
            把事实、推测和待核实的问题分别写清楚。笔记会保存在当前调查档案中。
          </p>
          <label htmlFor="notes">调查笔记</label>
          <Textarea
            id="notes"
            placeholder="我观察到…\n这可能意味着…\n还需要核实…"
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setDirty(true);
              setSaved(false);
            }}
            maxLength={4000}
            readOnly={!editable}
            className="notes-input"
          />
          <div className="writing-footer">
            <span>
              {notes.length} / 4000
              {dirty ? " · 有未保存的修改" : saved ? " · 已保存" : ""}
            </span>
            <Button
              disabled={!editable || pending || !dirty}
              onClick={() => act("notes", { notes }, "PUT")}
            >
              {pending ? (
                <Loader2 className="spin" size={16} />
              ) : (
                <Check size={16} />
              )}
              保存笔记
            </Button>
          </div>
          {saved && (
            <p role="status" className="saved-message">
              笔记已保存到档案。
            </p>
          )}
        </section>
      )}
      {tab === "verdict" && <Verdict session={s} pending={pending} act={act} />}
      <footer className="page-footer">
        {s.status === "Submitted"
          ? "档案已封存，可随时查阅。"
          : "你的进展会在每次成功操作后保存。"}
        <span>EchoCase / {statusLabel[s.status]}</span>
      </footer>
    </div>
  );
}

function Verdict({
  session: s,
  pending,
  act,
}: {
  session: Session;
  pending: boolean;
  act: (route: string, body?: unknown, method?: string) => void;
}) {
  const [suspect, setSuspect] = useState("林澈"),
    [reasoning, setReasoning] = useState("");
  const examined = s.evidence.filter((e) => e.examined),
    [support, setSupport] = useState<string[]>(examined.map((e) => e.id));
  if (s.verdict)
    return (
      <section className="verdict-result">
        <div className="result-check">
          <CheckCircle2 size={36} />
        </div>
        <span className="eyebrow">INVESTIGATION COMPLETE</span>
        <h2>结论已归档</h2>
        <p>你的结论与支持证据已封存，调查过程仍可随时查阅。</p>
        <div className="result-grid">
          <div>
            <span>责任人结论</span>
            <strong>{s.verdict.suspect}</strong>
          </div>
          <div>
            <span>证据完整性评估</span>
            <strong>
              {s.verdict.score}
              <small> / 100</small>
            </strong>
          </div>
        </div>
        <blockquote>{s.verdict.reasoning}</blockquote>
        <div className="support-tags">
          {s.verdict.supportingEvidence.map((id) => (
            <Badge variant="outline" key={id}>
              {s.evidence.find((e) => e.id === id)?.title}
            </Badge>
          ))}
        </div>
        <p className="subtle">
          这是基于固定案件规则的教学评估，分数仅反映本案的证据覆盖。
        </p>
      </section>
    );
  const ready = examined.length >= 3 && s.links.length >= 2;
  return (
    <section className="writing-panel verdict-panel">
      <span className="eyebrow">REVIEW BEFORE YOU CONCLUDE</span>
      <h2>先复核，再下结论。</h2>
      <p className="subtle">
        结论提交后档案将封存。请确认支持你的判断的证据已经形成完整链路。
      </p>
      <div className="review-checks">
        <span className={examined.length >= 3 ? "done" : ""}>
          <CheckCircle2 size={17} />
          至少调查三条证据 <b>{examined.length}/3</b>
        </span>
        <span className={s.links.length >= 2 ? "done" : ""}>
          <CheckCircle2 size={17} />
          至少建立两条关联 <b>{s.links.length}/2</b>
        </span>
      </div>
      {s.status === "Active" ? (
        <Button
          disabled={!ready || pending}
          onClick={() => act("state/review")}
        >
          进入复核
          <ArrowRight size={16} />
        </Button>
      ) : (
        <>
          <div className="review-banner">
            <ShieldCheck size={20} />
            <span>档案正在复核中。如需补充证据，请返回调查。</span>
            <button disabled={pending} onClick={() => act("state/resume")}>
              返回调查
            </button>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act("verdict", {
                suspect,
                reasoning,
                supportingEvidence: support,
              });
            }}
          >
            <label>
              责任人结论
              <select
                value={suspect}
                onChange={(e) => setSuspect(e.target.value)}
              >
                {["林澈", "周岚", "许舟"].map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </select>
            </label>
            <fieldset>
              <legend>支持证据（至少三条）</legend>
              {examined.map((e) => (
                <label className="check-label" key={e.id}>
                  <input
                    type="checkbox"
                    checked={support.includes(e.id)}
                    onChange={(event) =>
                      setSupport(
                        event.target.checked
                          ? [...support, e.id]
                          : support.filter((id) => id !== e.id),
                      )
                    }
                  />
                  {e.title}
                </label>
              ))}
            </fieldset>
            <label>
              结论说明
              <Textarea
                minLength={20}
                maxLength={4000}
                required
                value={reasoning}
                onChange={(e) => setReasoning(e.target.value)}
                placeholder="说明证据如何支持你的判断，并回应可能的矛盾。至少 20 字。"
              />
            </label>
            <Button
              type="submit"
              disabled={
                pending || support.length < 3 || reasoning.trim().length < 20
              }
            >
              <Scale size={17} />
              提交并封存结论
            </Button>
          </form>
        </>
      )}
    </section>
  );
}
