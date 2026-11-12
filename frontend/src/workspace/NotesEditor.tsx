import { BookOpen, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { Session } from "../api/client";
import type { Operation } from "./useInvestigation";
import { useNotesDraft } from "./useNotesDraft";

export default function NotesEditor({
  session,
  hidden,
  blocked,
  pending,
  operation,
  result,
  onSave,
}: {
  session: Session;
  hidden: boolean;
  blocked: boolean;
  pending: boolean;
  operation?: Operation;
  result?: Session;
  onSave: (op: Operation) => void;
}) {
  const draft = useNotesDraft(
    session,
    operation && result ? { result, operation } : undefined,
  );
  const editable = session.status === "Active";
  const optimistic =
    pending && operation?.kind === "notes" ? operation.body.notes : undefined;
  return (
    <section className="writing-panel" hidden={hidden}>
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
        value={draft.text}
        onChange={(e) => draft.edit(e.target.value)}
        maxLength={4000}
        readOnly={!editable}
        className="notes-input"
        placeholder="我观察到…\n这可能意味着…\n还需要核实…"
      />
      <div className="writing-footer">
        <span>
          {draft.text.length} / 4000
          {draft.dirty ? " · 有未保存的修改" : draft.saved ? " · 已保存" : ""}
        </span>
        <Button
          disabled={!editable || blocked || !draft.dirty || draft.conflict}
          onClick={() => onSave(draft.operation())}
        >
          {pending ? (
            <Loader2 className="spin" size={16} />
          ) : (
            <Check size={16} />
          )}
          保存笔记
        </Button>
      </div>
      {optimistic !== undefined && (
        <p className="subtle" data-testid="notes-pending">
          正在保存此快照：{optimistic}。可以继续编辑，后续输入会保留。
        </p>
      )}
      {draft.conflict && (
        <div className="notice" data-testid="notes-conflict">
          <p>
            档案已有较新版本。草稿基于版本 {draft.version}，当前版本{" "}
            {session.version}。请比较后决定。
          </p>
          <dl>
            <dt>编辑前的笔记</dt>
            <dd>{draft.baseline || "（空）"}</dd>
            <dt>当前已保存笔记</dt>
            <dd>{session.notes || "（空）"}</dd>
            <dt>本窗口草稿</dt>
            <dd>{draft.text || "（空）"}</dd>
          </dl>
          <Button
            disabled={!editable || blocked}
            onClick={() => onSave(draft.operation(true))}
          >
            确认保留草稿并基于当前版本保存
          </Button>
          <Button variant="outline" disabled={blocked} onClick={draft.discard}>
            采用服务器内容
          </Button>
        </div>
      )}
      {draft.saved && !draft.dirty && (
        <p role="status" className="saved-message">
          笔记已保存到档案。
        </p>
      )}
    </section>
  );
}
