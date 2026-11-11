# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase2a.spec.ts >> dirty draft keeps its baseline across refetch and requires explicit conflict confirmation
- Location: tests\phase2a.spec.ts:71:1

# Error details

```
Error: expect(locator).toBeDisabled() failed

Locator:  getByRole('button', { name: '保存笔记' })
Expected: disabled
Received: enabled
Timeout:  10000ms

Call log:
  - Expect "toBeDisabled" getByRole('button', { name: '保存笔记' }) with timeout 10000ms
  - waiting for getByRole('button', { name: '保存笔记' })
    23 × locator resolved to <button tabindex="0" type="button" data-slot="button" class="group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 da…>…</button>
       - unexpected value "enabled"

```

```yaml
- button "保存笔记"
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | import type { BrowserContext, Page } from "@playwright/test";
  3   | import { mkdir, writeFile } from "node:fs/promises";
  4   | 
  5   | const evidence = process.env.ECHOCASE_BROWSER_EVIDENCE ?? "../evidence/phase2a/browser";
  6   | let cookies: Awaited<ReturnType<BrowserContext["cookies"]>>;
  7   | test.beforeAll(async ({ browser, baseURL }) => {
  8   |   await mkdir(evidence, { recursive: true });
  9   |   const context = await browser.newContext({ baseURL });
  10  |   const csrf = (await (await context.request.get("/api/auth/csrf")).json()).token;
  11  |   const data = { email: `phase2a-${crypto.randomUUID()}@example.test`, password: "StrongLabPassword42" };
  12  |   for (const action of ["register", "login"]) {
  13  |     const r = await context.request.post(`/api/auth/${action}`, { data, headers: { "X-CSRF-TOKEN": csrf } });
  14  |     expect(r.status()).toBe(200);
  15  |   }
  16  |   cookies = await context.cookies();
  17  |   await context.close();
  18  | });
  19  | test.beforeEach(async ({ context, page }) => {
  20  |   await context.addCookies(cookies);
  21  |   await page.goto("/");
  22  |   await page.getByRole("button", { name: "开始新调查" }).click();
  23  |   await expect(page.getByRole("tab", { name: "证据档案" })).toBeVisible();
  24  | });
  25  | const url = (page: Page) => `/api/investigations/${new URL(page.url()).searchParams.get("case")}`;
  26  | const read = async (page: Page) => (await page.request.get(url(page))).json();
  27  | async function externalNotes(page: Page, notes: string) {
  28  |   const s = await read(page);
  29  |   const token = (await (await page.request.get("/api/auth/csrf")).json()).token;
  30  |   const r = await page.request.put(`${url(page)}/notes`, { data: { notes }, headers: {
  31  |     "X-CSRF-TOKEN": token, "Idempotency-Key": crypto.randomUUID(), "If-Match": `"${s.version}"`,
  32  |   } });
  33  |   expect(r.status()).toBe(200);
  34  |   return r.json();
  35  | }
  36  | async function record(page: Page, name: string, observation: unknown) {
  37  |   await writeFile(`${evidence}/${name}.json`, JSON.stringify(observation, null, 2));
  38  |   await page.screenshot({ path: `${evidence}/${name}.png`, fullPage: true });
  39  | }
  40  | 
  41  | test("draft typed while a real save response is delayed survives acknowledgement", async ({ page }) => {
  42  |   await page.getByRole("tab", { name: "调查笔记" }).click();
  43  |   const input = page.getByLabel("调查笔记", { exact: true });
  44  |   let release!: () => void;
  45  |   const hold = new Promise<void>((resolve) => { release = resolve; });
  46  |   let committed!: () => void;
  47  |   const sent = new Promise<void>((resolve) => { committed = resolve; });
  48  |   await page.route("**/api/investigations/*/notes", async (route) => {
  49  |     const response = await route.fetch(); // Real API commits before the response is held.
  50  |     committed();
  51  |     await hold;
  52  |     await route.fulfill({ response });
  53  |   });
  54  |   await input.fill("先提交的观察");
  55  |   await page.getByRole("button", { name: "保存笔记" }).click();
  56  |   await sent;
  57  |   await input.fill("先提交的观察；等待时继续记录的新线索");
  58  |   release();
  59  |   await expect(page.locator(".version-label")).toHaveText("档案版本 2");
  60  |   const server = await read(page);
  61  |   await record(page, "inflight-draft", { server, draft: await input.inputValue() });
  62  |   await expect(input).toHaveValue("先提交的观察；等待时继续记录的新线索");
  63  |   await expect(page.getByRole("button", { name: "保存笔记" })).toBeEnabled();
  64  |   expect(server.notes).toBe("先提交的观察");
  65  |   await page.unroute("**/api/investigations/*/notes");
  66  |   await page.getByRole("button", { name: "保存笔记" }).click();
  67  |   await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  68  |   expect((await read(page)).notes).toContain("继续记录");
  69  | });
  70  | 
  71  | test("dirty draft keeps its baseline across refetch and requires explicit conflict confirmation", async ({ page }) => {
  72  |   await page.getByRole("tab", { name: "调查笔记" }).click();
  73  |   const input = page.getByLabel("调查笔记", { exact: true });
  74  |   await input.fill("本窗口的待核实推断");
  75  |   const other = await externalNotes(page, "另一窗口已经核实的事实");
  76  |   await page.getByRole("button", { name: "刷新档案" }).click();
  77  |   await expect(page.locator(".version-label")).toHaveText(`档案版本 ${other.version}`);
  78  |   await record(page, "dirty-refetch", { server: await read(page), draft: await input.inputValue() });
  79  |   await expect(input).toHaveValue("本窗口的待核实推断");
> 80  |   await expect(page.getByRole("button", { name: "保存笔记" })).toBeDisabled();
      |                                                            ^ Error: expect(locator).toBeDisabled() failed
  81  |   await expect(page.getByTestId("notes-conflict")).toContainText("另一窗口已经核实的事实");
  82  |   await page.getByRole("button", { name: "确认保留草稿并基于当前版本保存" }).click();
  83  |   await expect(page.getByRole("status")).toHaveText("笔记已保存到档案。");
  84  |   expect((await read(page)).notes).toBe("本窗口的待核实推断");
  85  | });
  86  | 
  87  | test("committed write with lost response reuses its key and cannot regress a newer snapshot", async ({ page }) => {
  88  |   await page.getByRole("tab", { name: "调查笔记" }).click();
  89  |   const input = page.getByLabel("调查笔记", { exact: true });
  90  |   const attempts: { key?: string; version?: string; body: string | null }[] = [];
  91  |   let drop = true;
  92  |   await page.route("**/api/investigations/*/notes", async (route) => {
  93  |     const req = route.request();
  94  |     attempts.push({ key: req.headers()["idempotency-key"], version: req.headers()["if-match"], body: req.postData() });
  95  |     const response = await route.fetch();
  96  |     if (drop) { drop = false; await route.abort("connectionfailed"); }
  97  |     else await route.fulfill({ response });
  98  |   });
  99  |   await input.fill("提交成功但返回途中断开的观察");
  100 |   await page.getByRole("button", { name: "保存笔记" }).click();
  101 |   await expect(page.getByRole("alert")).toContainText("保存结果尚未确认");
  102 |   const committed = await read(page);
  103 |   expect(committed.notes).toBe("提交成功但返回途中断开的观察");
  104 |   // A later accepted write makes the stored receipt older than the current resource.
  105 |   const later = await externalNotes(page, "后来窗口补充的已保存事实");
  106 |   await page.getByRole("button", { name: "刷新档案" }).click();
  107 |   await expect(page.locator(".version-label")).toHaveText(`档案版本 ${later.version}`);
  108 |   const observedVersions: number[] = [];
  109 |   await page.exposeFunction("observeVersion", (v: string) => observedVersions.push(Number(v.replace(/\D/g, ""))));
  110 |   await page.locator(".version-label").evaluate((el) => {
  111 |     new MutationObserver(() => (window as unknown as { observeVersion: (v: string) => void }).observeVersion(el.textContent ?? "")).observe(el, { childList: true, subtree: true, characterData: true });
  112 |   });
  113 |   await page.getByRole("button", { name: "重试同一次操作" }).click();
  114 |   await expect(page.getByRole("button", { name: "重试同一次操作" })).toHaveCount(0);
  115 |   await expect(page.locator(".version-label")).toHaveText(`档案版本 ${later.version}`);
  116 |   await expect(input).toHaveValue("提交成功但返回途中断开的观察");
  117 |   expect(observedVersions.every((v) => v >= later.version)).toBe(true);
  118 |   expect(attempts).toHaveLength(2);
  119 |   expect(attempts[1]).toEqual(attempts[0]);
  120 |   expect((await read(page)).version).toBe(later.version);
  121 |   await record(page, "lost-response", { attempts, committed, later, observedVersions, final: await read(page) });
  122 | });
  123 | 
  124 | test("revise an existing link through the real graph editor without replacing its identity", async ({ page }) => {
  125 |   for (const title of ["异常门禁记录", "备用凭证领用册"]) {
  126 |     await page.getByRole("button", { name: `查看 ${title}`, exact: true }).click();
  127 |     await page.getByRole("button", { name: "调查此证据", exact: true }).click();
  128 |     await expect(page.locator(".evidence-body")).toBeVisible();
  129 |   }
  130 |   await page.getByRole("tab", { name: "关联图谱" }).click();
  131 |   await page.getByLabel("起点证据").selectOption("access-log");
  132 |   await page.getByLabel("终点证据").selectOption("badge-ledger");
  133 |   await page.getByRole("button", { name: "建立关联", exact: true }).click();
  134 |   await expect(page.getByRole("button", { name: "修订 access-log badge-ledger 关联", exact: true })).toBeVisible();
  135 |   const before = await read(page);
  136 |   await page.getByRole("button", { name: "修订 access-log badge-ledger 关联", exact: true }).click();
  137 |   await page.getByLabel("修订关联类型").selectOption("Contradicts");
  138 |   const rationale = "核对门禁时钟后发现领用时间与通行时间无法互相印证，暂改为存在矛盾。";
  139 |   await page.getByLabel("修订解释").fill(rationale);
  140 |   await page.getByRole("button", { name: "保存关联修订", exact: true }).click();
  141 |   await expect(page.getByText(rationale, { exact: true })).toBeVisible();
  142 |   const after = await read(page);
  143 |   expect(after.version).toBe(before.version + 1);
  144 |   expect(after.links[0]).toMatchObject({ ...before.links[0], kind: "Contradicts", rationale, revisedAt: expect.any(String) });
  145 |   await page.reload();
  146 |   await page.getByRole("tab", { name: "关联图谱" }).click();
  147 |   await expect(page.getByText(rationale, { exact: true })).toBeVisible();
  148 |   await record(page, "link-revision", { before, after });
  149 | });
  150 | 
```