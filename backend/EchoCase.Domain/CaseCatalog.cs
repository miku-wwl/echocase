namespace EchoCase.Domain;

public sealed record EvidenceDefinition(string Id, string Title, string Kind, string Summary, string Body, string? Requires = null);
public sealed record CaseDefinition(string Id, string Title, string Subtitle, string Synopsis, string[] Suspects, IReadOnlyList<EvidenceDefinition> Evidence);

public static class CaseCatalog
{
    public const string CaseId = "harbor-01";
    public static readonly CaseDefinition Harbor = new(CaseId, "雾港档案", "THE HARBOR FILE · EC-001",
        "凌晨 02:17，雾港档案室的一份航运账册失踪。门禁、摄像与值班记录彼此矛盾。你需要重建时间线，用可核对的证据支持结论。所有人物与事件均为虚构。",
        ["林澈", "周岚", "许舟"],
        [new("access-log", "异常门禁记录", "系统日志", "02:12，有人使用档案室的备用凭证。", "门禁记录：02:12:06，凭证 B-17 从西门进入；02:19:41 离开。记录完整，未出现系统重启。"),
         new("camera", "走廊摄像片段", "影像记录", "02:09 至 02:21 的画面中断。", "摄像机在 02:09 收到远程维护指令，02:21 恢复。画面中断不能直接证明有人进入档案室。"),
         new("badge-ledger", "备用凭证领用册", "书面档案", "核对 B-17 的保管责任人。", "当天 18:30，林澈签领 B-17；次日 08:00 归还。周岚使用 B-05，许舟未领用备用凭证。", "access-log"),
         new("maintenance", "维护工单", "运维记录", "摄像维护与门禁异常是否有关？", "维护工单经周岚于前日审批，自动任务在 02:09 执行。维护不会停用门禁。摄像中断有独立原因。"),
         new("dispatch", "调度消息副本", "通信记录", "与凭证保管人有关的消息副本。", "01:58，林澈发送消息：『我用 B-17 取出账册，02:20 前离开。』副本来自已签名的归档，时间与门禁记录一致。", "badge-ledger"),
         new("witness", "值班人员笔录", "访谈记录", "证人把时间记成了 02:40。", "许舟称 02:40 看见有人离开西门；值班钟比标准时间快 21 分钟。校正后为 02:19，与门禁时间一致。")]);

    public static CaseDefinition Get(string id) => id == CaseId ? Harbor : throw new DomainRule("case_not_found", "案件不存在。");
    public static EvidenceDefinition Evidence(string id) => Harbor.Evidence.FirstOrDefault(x => x.Id == id)
        ?? throw new DomainRule("evidence_not_found", "证据不存在。");
    public static int Evaluate(string suspect, IReadOnlyCollection<string> support) =>
        suspect == "林澈" && new[] { "access-log", "badge-ledger", "dispatch" }.All(support.Contains) ? 100 : 40;
}
