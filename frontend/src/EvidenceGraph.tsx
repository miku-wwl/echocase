import { useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  applyNodeChanges,
} from "@xyflow/react";
import type { Node, Edge, Connection } from "@xyflow/react";
import { Network, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Session } from "./api/client";
import "@xyflow/react/dist/style.css";
import LinkEditor from "./workspace/LinkEditor";
import type { ReviseLinkRequest } from "./api/client";
export default function EvidenceGraph({
  session,
  disabled,
  onLink,
  onRemove,
  onRevise,
}: {
  session: Session;
  disabled: boolean;
  onLink: (s: string, t: string, k: string) => void;
  onRemove: (id: string) => void;
  onRevise: (
    id: string,
    body: ReviseLinkRequest,
    version: number,
  ) => Promise<unknown>;
}) {
  const evidence = session.evidence.filter((e) => e.examined);
  const [nodes, setNodes] = useState<Node[]>([]),
    [source, setSource] = useState(""),
    [target, setTarget] = useState(""),
    [kind, setKind] = useState("Corroborates"),
    [selected, setSelected] = useState<string | null>(null);
  useEffect(() => {
    setNodes((old) =>
      evidence.map((e, index) => ({
        id: e.id,
        position: old.find((n) => n.id === e.id)?.position ?? {
          x: 60 + (index % 3) * 260,
          y: 70 + Math.floor(index / 3) * 190,
        },
        data: { label: e.title },
        style: {
          background: "#fff",
          color: "#163b42",
          border: "1px solid #88a9a5",
          borderRadius: 9,
          width: 190,
          padding: 20,
          fontSize: 13,
          boxShadow: "0 4px 14px #173b4210",
        },
      })),
    );
  }, [session.version]); // Positions are local presentation state.
  const edges: Edge[] = session.links.map((l) => ({
    id: l.id,
    source: l.sourceId,
    target: l.targetId,
    label: l.kind === "Corroborates" ? "相互印证" : "存在矛盾",
    type: "smoothstep",
    animated: false,
    style: {
      stroke: l.kind === "Corroborates" ? "#4b8378" : "#b66848",
      strokeWidth: selected === l.id ? 3 : 1.8,
    },
    labelStyle: { fill: "#163b42", fontSize: 12 },
  }));
  const connect = (c: Connection) => {
    if (!disabled && c.source && c.target) onLink(c.source, c.target, kind);
  };
  return (
    <div className="graph-panel">
      <div className="graph-toolbar">
        <label>
          起点证据
          <select
            aria-label="起点证据"
            disabled={disabled}
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">选择证据</option>
            {evidence.map((e) => (
              <option value={e.id} key={e.id}>
                {e.title}
              </option>
            ))}
          </select>
        </label>
        <span>→</span>
        <label>
          终点证据
          <select
            aria-label="终点证据"
            disabled={disabled}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">选择证据</option>
            {evidence.map((e) => (
              <option value={e.id} key={e.id}>
                {e.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          关联类型
          <select
            aria-label="关联类型"
            value={kind}
            disabled={disabled}
            onChange={(e) => setKind(e.target.value)}
          >
            <option value="Corroborates">相互印证</option>
            <option value="Contradicts">存在矛盾</option>
          </select>
        </label>
        <Button
          disabled={disabled || !source || !target || source === target}
          onClick={() => onLink(source, target, kind)}
        >
          建立关联
        </Button>
      </div>
      <div className="graph-canvas" data-testid="evidence-graph">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={(changes) =>
            setNodes((n) => applyNodeChanges(changes, n))
          }
          onConnect={connect}
          nodesConnectable={!disabled}
          onEdgeClick={(_, edge) => setSelected(edge.id)}
          fitView
          minZoom={0.3}
          maxZoom={1.5}
          aria-label="证据关联图"
        >
          <Background gap={24} color="#cbd6d3" />
          <Controls showInteractive={false} />
        </ReactFlow>
        {!evidence.length && (
          <div className="graph-empty">
            <Network size={36} />
            <h3>还没有可关联的线索</h3>
            <p>先调查两条证据，再来建立它们的联系。</p>
          </div>
        )}
      </div>
      <div className="graph-legend">
        <span>
          <i />
          相互印证
        </span>
        <span>
          <i className="contradict" />
          存在矛盾
        </span>
        <small>布局仅在当前视图保留；关联会保存到档案。</small>
        {selected && !disabled && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onRemove(selected);
              setSelected(null);
            }}
          >
            <Trash2 size={14} />
            删除选中关联
          </Button>
        )}
      </div>
      <div className="link-list">
        {session.links.map((l) => (
          <div key={l.id} className="link-row">
            <span>{evidence.find((e) => e.id === l.sourceId)?.title}</span>
            <b>{l.kind === "Corroborates" ? "相互印证" : "存在矛盾"}</b>
            <span>{evidence.find((e) => e.id === l.targetId)?.title}</span>
            <LinkEditor
              link={l}
              version={session.version}
              disabled={disabled}
              onSave={onRevise}
            />
            {l.rationale && <p className="link-rationale">{l.rationale}</p>}
            {!disabled && (
              <button
                aria-label={`删除 ${l.sourceId} ${l.targetId} 关联`}
                onClick={() => onRemove(l.id)}
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
