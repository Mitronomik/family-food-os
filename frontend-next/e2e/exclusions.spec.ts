import { test, expect, type Page } from "@playwright/test";
const H="11111111-1111-4111-8111-111111111111";
const A="22222222-2222-4222-8222-222222222222";
const B="33333333-3333-4333-8333-333333333333";
const C="44444444-4444-4444-8444-444444444444";
const D="55555555-5555-4555-8555-555555555555";
const E="66666666-6666-4666-8666-666666666666";
const F="77777777-7777-4777-8777-777777777777";
const foods=[{id:C,canonical_name:"Морковь",is_active:false},{id:D,canonical_name:"Говядина",is_active:true},{id:E,canonical_name:"Свёкла",is_active:true}];
type Hook = (resource: string) => number | void | Promise<number | void>;
type FixtureOptions = {
  start?: boolean;
  household?: Hook;
  member?: Hook;
  food?: Hook;
  search?: Hook;
  includeInactiveMember?: boolean;
};

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>(done => { resolve = done; });
  return { promise, resolve };
}

async function fixture(page: Page, options: FixtureOptions = {}) {
  const sets: Record<string, string[]> = { [A]: [C], [B]: [], [F]: [C] };
  const catalogue = foods.map(food => ({ ...food }));
  const writes:unknown[]=[];
  let failure=0;
  let delay=0;
  await page.route("**/api/**", async route=>{
    const req=route.request();const url=new URL(req.url());const path=url.pathname;
    if (path === "/api/households/" + H) {
      const code = await options.household?.(H);
      if (code) return route.fulfill({ status: code, json: { detail: "private" } });
      const members = [{ id: A, name: "Анна", active: true }, { id: B, name: "Борис", active: true }];
      if (options.includeInactiveMember) members.push({ id: F, name: "Вера", active: false });
      return route.fulfill({ json: { id: H, name: "Тестовая семья", members } });
    }
    if(path.endsWith("/food-exclusions")){
      const member=path.split("/")[5];
      if(req.method()==="PUT"){
        const body=req.postDataJSON();writes.push(body);
        if(delay) await new Promise(r=>setTimeout(r,delay));
        if(failure===-1)return route.abort("failed");
        if(failure)return route.fulfill({status:failure,json:{detail:"private"}});
        if(JSON.stringify([...body.expected_excluded_food_ingredient_ids].sort())!==JSON.stringify([...sets[member]].sort()))return route.fulfill({status:409,json:{}});
        sets[member]=body.excluded_food_ingredient_ids;
        return route.fulfill({json:{excluded_food_ingredient_ids:sets[member],changed:true}});
      }
      const code = await options.member?.(member);
      if (code) return route.fulfill({ status: code, json: { detail: "private" } });
      return route.fulfill({ json: { excluded_food_ingredient_ids: sets[member] } });
    }
    if(path==="/api/food-ingredients"){
      const q=url.searchParams.get("q")||"";
      const code = await options.search?.(q);
      if (code) return route.fulfill({ status: code, json: { detail: "private" } });
      const items=q==="медленно"?[catalogue[2]]:catalogue.filter(f=>f.is_active&&(f.canonical_name.toLowerCase().includes(q.toLowerCase())||(q==="мясо"&&f.id===D)));
      return route.fulfill({json:{items}});
    }
    const id = path.split("/").at(-1) ?? "";
    const code = await options.food?.(id);
    if (code) return route.fulfill({ status: code, json: { detail: "private" } });
    const food = catalogue.find(item => item.id === id);
    return route.fulfill(food ? { json: food } : { status: 404, json: {} });
  });
  if (options.start !== false) {
    await page.goto("/?household=" + H);
    await expect(page.getByRole("heading", { name: "Не используем" })).toBeVisible();
    await expect(page.getByText("Морковь", { exact: true })).toBeVisible();
  }
  return { sets, writes, catalogue, fail: (code: number) => { failure = code; },
    delay: (ms: number) => { delay = ms; } };
}
test("member isolation, alias, inactive retention, CAS and reload",async({page})=>{
  const f=await fixture(page);
  await expect(page.getByRole("button",{name:"Сохранить",exact:true})).toBeDisabled();
  await page.getByRole("searchbox").fill("мясо");
  await page.getByRole("button",{name:"Добавить: Говядина"}).click();
  await expect(page.getByRole("button",{name:"Добавить: Говядина"})).toBeDisabled();
  await page.getByRole("button",{name:"Борис"}).click();
  await expect(page.getByText("Нет исключённых продуктов.",{exact:false})).toBeVisible();
  await page.getByRole("button",{name:/Анна/}).click();
  await expect(page.getByText("Говядина",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.writes).toEqual([{expected_excluded_food_ingredient_ids:[C],excluded_food_ingredient_ids:[C,D]}]);
  await page.reload();
  await expect(page.getByText("Морковь",{exact:true})).toBeVisible();
  await expect(page.getByText("Говядина",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Удалить: Морковь"}).click();
  await page.getByRole("button",{name:"Удалить: Говядина"}).click();
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.sets[A]).toEqual([]);
});
test("conflict requires explicit review, no blind overwrite",async({page})=>{
  const f=await fixture(page);
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button",{name:"Добавить: Говядина"}).click();
  f.sets[A]=[C,E];
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByText(/Список изменился/)).toBeVisible();
  expect(f.writes.length).toBe(1);
  await page.getByRole("button",{name:"Обновить актуальный список"}).click();
  await page.getByRole("button",{name:"Перенести мои изменения"}).click();
  expect(f.writes.length).toBe(1);
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.sets[A]).toEqual([C,D,E]);
});
for(const code of [404,422,503,-1])test("safe save failure "+code,async({page})=>{
  let failStatusRead = false;
  const f = await fixture(page, { household: () => failStatusRead ? 503 : undefined });
  await page.getByRole("button",{name:"Удалить: Морковь"}).click();
  f.fail(code);
  failStatusRead = code === 422;
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  const failureText = ({ 404: "не найден", 422: "Не удалось проверить",
    503: "временно недоступно", [-1]: "Не удалось связаться" })[code]!;
  const alerts = page.getByRole("main").getByRole("alert");
  await expect(alerts.filter({ hasText: failureText })).toBeVisible();
  await expect(page.getByText("Не сохранено",{exact:true}).first()).toBeVisible();
  await expect(page.getByText(/Изменения сохранены/)).toHaveCount(0);
  expect(f.sets[A]).toEqual([C]);
  await expect(page.getByText("private",{exact:true})).toHaveCount(0);
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  if (code === 503 || code === -1) {
    await expect(save).toBeDisabled();
    await page.getByRole("button", { name: "Обновить актуальный список" }).click();
    await page.getByRole("button", { name: "Перенести мои изменения" }).click();
    expect(f.writes).toHaveLength(1);
  }
  if (code === 422) {
    await expect(alerts.filter({ hasText: "Загрузка временно недоступна" })).toBeVisible();
    await expect(save).toBeDisabled();
    await expect(page.getByRole("searchbox")).toBeDisabled();
    failStatusRead = false;
    await page.getByRole("button", { name: "Проверить статус участника" }).click();
    await expect(save).toBeEnabled();
    expect(f.writes).toHaveLength(1);
  }
  f.fail(0);
  await save.click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.sets[A]).toEqual([]);
});
test("save blocks switching and stale search does not win",async({page})=>{
  const started = deferred();
  const release = deferred();
  const f = await fixture(page, { search: async query => {
    if (query !== "медленно") return;
    started.resolve();
    await release.promise;
  } });
  await page.getByRole("searchbox").fill("медленно");
  await started.promise;
  await expect(page.getByRole("status").filter({ hasText: "Ищем продукты" })).toBeVisible();
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button",{name:"Добавить: Говядина"}).click();
  release.resolve();
  await expect(page.getByRole("button",{name:"Добавить: Свёкла"})).toHaveCount(0);
  f.delay(800);
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByRole("button",{name:"Борис"})).toBeDisabled();
  await expect(page.getByRole("button", { name: "Сохраняем…" })).toBeDisabled();
  await expect(page.getByRole("searchbox")).toBeDisabled();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.writes).toHaveLength(1);
});
for(const width of [375,390,430,768,1024,1440])test("responsive "+width,async({page},info)=>{
  await page.setViewportSize({width,height:900});await fixture(page);
  await page.getByRole("searchbox").fill("говядина");
  await expect(page.getByRole("button",{name:"Добавить: Говядина"})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.getByRole("searchbox").focus();
  await page.keyboard.press("Tab");
  const add = page.getByRole("button", { name: "Добавить: Говядина" });
  await expect(add).toBeFocused();
  await expect(add).toHaveCSS("outline-style", "solid");
  await expect(add).toHaveCSS("outline-width", "3px");
  await page.keyboard.press("Enter");
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  await expect(save).toBeEnabled();
  await page.keyboard.press("Tab");
  await expect(save).toBeFocused();
  await expect(save).toHaveCSS("outline-width", "3px");
  await page.screenshot({ path: info.outputPath("viewport-" + width + ".png"), fullPage: true });
  await page.keyboard.press("Enter");
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
});

test("loading, retry, search error and empty states", async ({ page }) => {
  const householdReady = deferred();
  const selectionReady = deferred();
  let householdCalls = 0;
  let memberCalls = 0;
  await fixture(page, {
    start: false,
    household: async () => {
      if (++householdCalls === 1) { await householdReady.promise; return 503; }
    },
    member: async () => {
      if (++memberCalls === 1) { await selectionReady.promise; return 404; }
    },
    search: query => query === "ошибка" ? 503 : undefined,
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Семья не выбрана" })).toBeVisible();
  await page.goto("/?household=" + H);
  await expect(page.getByRole("status")).toContainText("Загружаем семью");
  householdReady.resolve();
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Повторить загрузку семьи" }).click();
  await expect(page.getByRole("status")).toContainText("Загружаем исключения");
  selectionReady.resolve();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("не найден");
  await page.getByRole("button", { name: "Повторить загрузку исключений" }).click();
  await expect(page.getByRole("button", { name: "Удалить: Морковь" })).toBeVisible();
  await page.getByRole("searchbox").fill("ошибка");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Не удалось выполнить поиск");
  await page.getByRole("searchbox").fill("неизвестный продукт");
  await expect(page.getByRole("status")).toContainText("Ничего не найдено");
  await expect(page.getByText("private", { exact: true })).toHaveCount(0);
});

test("late member metadata cannot overwrite the current draft", async ({ page }) => {
  const started = deferred();
  const release = deferred();
  const finished = deferred();
  await fixture(page, {
    start: false,
    food: async id => {
      if (id !== C) return;
      started.resolve();
      await release.promise;
      finished.resolve();
    },
  });
  await page.goto("/?household=" + H);
  await started.promise;
  await page.getByRole("button", { name: "Борис" }).click();
  await expect(page.getByText(/Нет исключённых продуктов/)).toBeVisible();
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  release.resolve();
  await finished.promise;
  await expect(page.getByRole("button", { name: "Удалить: Говядина" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Удалить: Морковь" })).toHaveCount(0);
  await page.getByRole("button", { name: "Анна" }).click();
  await expect(page.getByRole("button", { name: "Удалить: Морковь" })).toBeVisible();
  await page.getByRole("button", { name: /Борис/ }).click();
  await expect(page.getByRole("button", { name: "Удалить: Говядина" })).toBeVisible();
});

test("reconciliation keeps unavailable additions visible and blocks their save", async ({ page }) => {
  const f = await fixture(page);
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  f.catalogue.find(food => food.id === D)!.is_active = false;
  f.fail(409);
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  await save.click();
  await page.getByRole("button", { name: "Обновить актуальный список" }).click();
  await page.getByRole("button", { name: "Перенести мои изменения" }).click();
  await expect(page.getByText("Нельзя добавить в исключения")).toBeVisible();
  await expect(save).toBeDisabled();
  await page.getByRole("button", { name: "Удалить: Говядина" }).click();
  await expect(save).toBeDisabled();
  expect(f.writes).toHaveLength(1);
  expect(f.sets[A]).toEqual([C]);

  await page.getByRole("searchbox").fill("свёкла");
  await page.getByRole("button", { name: "Добавить: Свёкла" }).click();
  f.sets[A] = [];
  await save.click();
  await page.getByRole("button", { name: "Обновить актуальный список" }).click();
  await expect(page.getByText("Сохранённых исключений нет.")).toBeVisible();
  await page.getByRole("button", { name: "Оставить актуальный список" }).click();
  await expect(page.getByText(/Нет исключённых продуктов/)).toBeVisible();
  await expect(save).toBeDisabled();
  expect(f.writes).toHaveLength(2);
});

test("unreadable catalogue metadata stays selected and inactive members are read-only", async ({ page }) => {
  const f = await fixture(page, {
    start: false, includeInactiveMember: true, food: id => id === C ? 404 : undefined,
  });
  await page.goto("/?household=" + H);
  await expect(page.getByRole("button", { name: "Удалить: Название недоступно" })).toBeVisible();
  await expect(page.getByText(C)).toHaveCount(0);
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(f.sets[A]).toEqual([C, D]);
  await page.getByRole("button", { name: /Вера/ }).click();
  await expect(page.getByRole("status").filter({ hasText: "Участник неактивен" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Удалить: Название недоступно" })).toBeDisabled();
  await expect(page.getByRole("searchbox")).toBeDisabled();
});

test("leaving with unsaved changes warns and keeps the draft", async ({ page }) => {
  await fixture(page);
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  const remove = page.getByRole("button", { name: "Удалить: Морковь" });
  await remove.click();
  await expect(save).toBeEnabled();
  const warned = page.waitForEvent("dialog").then(async dialog => {
    expect(dialog.type()).toBe("beforeunload");
    await dialog.dismiss();
  });
  await Promise.all([warned, page.evaluate(() => { window.location.assign("/"); })]);
  await expect(page).toHaveURL("/?household=" + H);
  await expect(save).toBeEnabled();
  await save.click();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(await page.evaluate(() =>
    window.dispatchEvent(new Event("beforeunload", { cancelable: true })),
  )).toBe(true);
});
