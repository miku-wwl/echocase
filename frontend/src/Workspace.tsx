import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  Circle,
  FileSearch,
  GitBranch,
  Loader2,
  LockKeyhole,
  Network,
  RefreshCw,
  Scale,
  Search,
  ShieldCheck,
  StickyNote,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import type { Action, Evidence, Session, User } from "./api/client";
import Message from "./components/Message";
import EvidenceGraph from "./EvidenceGraph";
import { useInvestigation } from "./workspace/useInvestigation";
import NotesEditor from "./workspace/NotesEditor";
const statusLabel: Record<string, string> = {
  Active: "调查中",
  Reviewing: "复核中",
  Submitted: "已结案",
};
export default function Workspace({
  id,
  user,
  onBack,
}: {
  id: string;
  user: User;
  onBack: () => void;
}) {
  const { query, mutation, act, blocked, uncertain } = useInvestigation(
    id,
    user.id,
  );
  const [tab, setTab] = useState("evidence"),
    [selected, setSelected] = useState<Evidence | null>(null);
  const s = query.data;
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
    pending = blocked;
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
      {uncertain && (
        <Button
          variant="outline"
          disabled={mutation.isPending}
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
                        act({ kind: "examine", evidenceId: currentSelected.id })
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
              act({ kind: "link", body: { sourceId, targetId, kind } })
            }
            onRemove={(linkId) => act({ kind: "unlink", linkId })}
            onRevise={(linkId, body, version) =>
              mutation.mutateAsync({
                kind: "revise-link",
                linkId,
                body,
                version,
                key: crypto.randomUUID(),
              })
            }
          />
        </section>
      )}
      <NotesEditor
        session={s}
        hidden={tab !== "notes"}
        blocked={blocked}
        pending={mutation.isPending}
        operation={mutation.variables}
        result={mutation.isSuccess ? mutation.data : undefined}
        onSave={(op) => mutation.mutate(op)}
      />
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
  act: (action: Action) => void;
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
          onClick={() => act({ kind: "transition", action: "review" })}
        >
          进入复核
          <ArrowRight size={16} />
        </Button>
      ) : (
        <>
          <div className="review-banner">
            <ShieldCheck size={20} />
            <span>档案正在复核中。如需补充证据，请返回调查。</span>
            <button
              disabled={pending}
              onClick={() => act({ kind: "transition", action: "resume" })}
            >
              返回调查
            </button>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act({
                kind: "verdict",
                body: {
                  suspect,
                  reasoning,
                  supportingEvidence: support,
                },
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
