import { devices, expect, test, type APIRequestContext, type APIResponse } from "@playwright/test";

const householdId = "11111111-1111-4111-8111-111111111111";
const backend = "http://127.0.0.1:8000";
type Member = { id: string; name: string };
type Selection = { excluded_food_ingredient_ids: string[] };

async function readJson<T>(response: APIResponse): Promise<T> {
  expect(response.ok(), `API status for ${response.url()}`).toBe(true);
  return response.json() as Promise<T>;
}

test("real FastAPI persists isolated member exclusions and rejects stale saves", async ({
  page, request, browser,
}, info) => {
  const householdApi = `${backend}/api/households/${householdId}`;
  const { members } = await readJson<{ members: Member[] }>(await request.get(householdApi));
  const anna = members.find(member => member.name === "Анна")!;
  const boris = members.find(member => member.name === "Борис")!;
  const annaApi = `${householdApi}/members/${anna.id}/food-exclusions`;
  const borisApi = `${householdApi}/members/${boris.id}/food-exclusions`;
  const selection = async (url: string) =>
    (await readJson<Selection>(await request.get(url))).excluded_food_ingredient_ids;
  const catalogueId = async (q: string) => {
    const { items } = await readJson<{ items: { id: string }[] }>(
      await request.get(`${backend}/api/food-ingredients`, { params: { q } }),
    );
    expect(items).toHaveLength(1);
    return items[0].id;
  };
  const [carrot] = await selection(annaApi);
  const beef = await catalogueId("тестовый мясной продукт");
  const beet = await catalogueId("свёкла");
  expect(carrot).toBeDefined();
  expect(await selection(borisApi)).toEqual([]);

  const path = `/?household=${householdId}`;
  await page.setViewportSize({ width: 1440, height: 900 });
  const navigation = await page.goto(path);
  expect(navigation?.headers()["cache-control"]).toContain("no-store");
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  const saved = page.getByRole("region", { name: "Выбрано", exact: false });
  await expect(saved.getByText("Морковь")).toBeVisible();
  await expect(saved.getByText(/Больше не в каталоге/)).toBeVisible();

  const search = page.getByRole("searchbox");
  await search.fill("ТЕСТОВЫЙ МЯСНОЙ ПРОДУКТ");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  await page.getByRole("button", { name: "Борис", exact: true }).click();
  await expect(page.getByText(/Нет исключённых продуктов/)).toBeVisible();
  await page.getByRole("button", { name: /Анна/ }).click();
  await expect(saved.getByText("Говядина")).toBeVisible();
  expect(await selection(annaApi)).toEqual([carrot]);

  await readJson(await request.put(annaApi, { data: {
    expected_excluded_food_ingredient_ids: [carrot],
    excluded_food_ingredient_ids: [carrot, beet],
  } }));
  const initialSave = page.waitForResponse(response =>
    response.url().endsWith("/food-exclusions") && response.request().method() === "PUT");
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  expect((await initialSave).status()).toBe(409);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Список изменился");
  await page.getByRole("button", { name: "Обновить актуальный список" }).click();
  await expect(page.getByRole("region", { name: "Проверка актуального списка" }))
    .toContainText("Свёкла");
  await page.getByRole("button", { name: "Перенести мои изменения" }).click();
  expect(await selection(annaApi)).toEqual([carrot, beet].sort());

  const confirmed = page.waitForResponse(response =>
    response.url().endsWith("/food-exclusions") && response.request().method() === "PUT");
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  const response = await confirmed;
  expect(response.status()).toBe(200);
  expect(response.headers()["cache-control"]).toContain("no-store");
  expect(response.request().postDataJSON()).toEqual({
    expected_excluded_food_ingredient_ids: [carrot, beet].sort(),
    excluded_food_ingredient_ids: [carrot, beef, beet].sort(),
  });
  await expect(page.getByRole("status")).toContainText("Изменения сохранены");
  await expect(saved.getByText("Свёкла")).toBeVisible();
  expect(await selection(annaApi)).toEqual([carrot, beef, beet].sort());
  expect(await selection(borisApi)).toEqual([]);

  await search.fill("мясной");
  await expect(page.getByRole("button", { name: "Добавить: Говядина" })).toBeDisabled();
  await page.screenshot({ path: info.outputPath("real-backend-desktop-1440.png"), fullPage: true });

  const mobile = await browser.newContext({
    ...devices["Pixel 7"],
    viewport: { width: 390, height: 844 },
  });
  try {
    const phone = await mobile.newPage();
    await phone.goto(new URL(path, page.url()).href);
    await phone.getByRole("button", { name: "Анна", exact: true }).click();
    for (const name of ["Морковь", "Говядина", "Свёкла"]) {
      await expect(phone.getByRole("button", { name: `Удалить: ${name}` })).toBeVisible();
    }
    expect(await phone.evaluate(() => ({
      width: window.innerWidth,
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      local: localStorage.length,
      session: sessionStorage.length,
    }))).toEqual({ width: 390, overflow: false, local: 0, session: 0 });
    await phone.screenshot({ path: info.outputPath("real-backend-phone-390.png"), fullPage: true });
  } finally {
    await mobile.close();
  }

  await page.reload();
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  for (const name of ["Морковь", "Говядина", "Свёкла"]) {
    await page.getByRole("button", { name: `Удалить: ${name}` }).click();
  }
  await page.getByRole("button", { name: "Сохранить", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Изменения сохранены");
  expect(await selection(annaApi)).toEqual([]);
  expect(await selection(borisApi)).toEqual([]);
  await search.fill("морковь");
  await expect(page.getByRole("status").filter({ hasText: "Ничего не найдено" })).toBeVisible();
});

async function createReviewHousehold(request: APIRequestContext) {
  const { id } = await readJson<{ id: string }>(await request.post(backend + "/api/households", {
    data: { name: "Тестовая семья", timezone: "Europe/Moscow" },
  }));
  const api = backend + "/api/households/" + id;
  const addMember = async (name: string) => {
    const member = await readJson<Member>(await request.post(api + "/members", {
      data: { name, activity_level: "moderate", goal: "maintain" },
    }));
    return api + "/members/" + member.id;
  };
  const anna = await addMember("Анна");
  const boris = await addMember("Борис");
  return { path: "/?household=" + id, anna, boris };
}

test("a lost response after a real commit requires review before further edits", async ({ page, request }) => {
  const { path, anna } = await createReviewHousehold(request);
  const endpoint = anna + "/food-exclusions";
  const readSelection = async () =>
    (await readJson<Selection>(await request.get(endpoint))).excluded_food_ingredient_ids;
  let putCount = 0;
  let committedStatus: number | undefined;
  await page.route(url => url.pathname === new URL(endpoint).pathname, async route => {
    if (route.request().method() !== "PUT" || ++putCount !== 1) {
      await route.continue();
      return;
    }
    // Deliver the original PUT to the real API and lose only the browser's response.
    const response = await route.fetch({ maxRetries: 0 });
    committedStatus = response.status();
    await route.abort("failed");
  });

  await page.goto(path);
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  const remove = page.getByRole("button", { name: "Удалить: Говядина" });
  await save.click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Не удалось связаться");
  expect(committedStatus).toBe(200);
  const committed = await readSelection();
  expect(committed).toHaveLength(1);
  await expect(remove).toBeDisabled();
  await expect(page.getByRole("searchbox")).toBeDisabled();
  await expect(save).toBeDisabled();

  await page.getByRole("button", { name: "Обновить актуальный список" }).click();
  await expect(page.getByRole("region", { name: "Проверка актуального списка" }))
    .toContainText("Говядина");
  await page.getByRole("button", { name: "Перенести мои изменения" }).click();
  await expect(remove).toBeEnabled();
  await expect(save).toBeDisabled();
  expect(putCount).toBe(1);
  expect(await readSelection()).toEqual(committed);

  await remove.click();
  const saved = page.waitForResponse(response =>
    response.url().endsWith("/food-exclusions") && response.request().method() === "PUT");
  await save.click();
  const response = await saved;
  expect(response.status()).toBe(200);
  expect(response.request().postDataJSON()).toEqual({
    expected_excluded_food_ingredient_ids: committed,
    excluded_food_ingredient_ids: [],
  });
  await expect(page.getByRole("status")).toContainText("Изменения сохранены");
  expect(putCount).toBe(2);
  expect(await readSelection()).toEqual([]);
});

test("a real deactivation makes the stale draft read-only after 422", async ({ page, request }) => {
  const { path, anna, boris } = await createReviewHousehold(request);
  const endpoint = anna + "/food-exclusions";
  const save = page.getByRole("button", { name: "Сохранить", exact: true });
  let annaWrites = 0;
  page.on("request", incoming => {
    if (incoming.method() === "PUT" && new URL(incoming.url()).pathname === new URL(endpoint).pathname) {
      annaWrites++;
    }
  });
  await page.goto(path);
  await page.getByRole("button", { name: "Борис", exact: true }).click();
  await page.getByRole("searchbox").fill("свёкла");
  await page.getByRole("button", { name: "Добавить: Свёкла" }).click();
  await page.getByRole("button", { name: "Анна", exact: true }).click();
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button", { name: "Добавить: Говядина" }).click();

  expect(await readJson<{ active: boolean }>(await request.patch(anna, {
    data: { active: false },
  }))).toMatchObject({ active: false });
  const failed = page.waitForResponse(response =>
    new URL(response.url()).pathname === new URL(endpoint).pathname && response.request().method() === "PUT");
  await save.click();
  expect((await failed).status()).toBe(422);
  await expect(page.getByRole("status").filter({ hasText: "Участник неактивен" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Удалить: Говядина" })).toBeDisabled();
  await expect(page.getByRole("searchbox")).toBeDisabled();
  await expect(save).toBeDisabled();

  await page.getByRole("button", { name: /^Борис/ }).click();
  await expect(page.getByRole("button", { name: "Удалить: Свёкла" })).toBeEnabled();
  await expect(save).toBeEnabled();
  await page.getByRole("button", { name: /^Анна.*Неактивен/ }).click();
  await expect(page.getByRole("button", { name: "Удалить: Говядина" })).toBeDisabled();
  await expect(save).toBeDisabled();
  expect(annaWrites).toBe(1);
  for (const url of [endpoint, boris + "/food-exclusions"]) {
    expect(await readJson<Selection>(await request.get(url))).toEqual({ excluded_food_ingredient_ids: [] });
  }
});
