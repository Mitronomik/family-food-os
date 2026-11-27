import { test, expect, type Page } from "@playwright/test";
const H="11111111-1111-4111-8111-111111111111";
const A="22222222-2222-4222-8222-222222222222";
const B="33333333-3333-4333-8333-333333333333";
const C="44444444-4444-4444-8444-444444444444";
const D="55555555-5555-4555-8555-555555555555";
const E="66666666-6666-4666-8666-666666666666";
const foods=[{id:C,canonical_name:"Морковь",is_active:false},{id:D,canonical_name:"Говядина",is_active:true},{id:E,canonical_name:"Свёкла",is_active:true}];
async function fixture(page:Page) {
  const sets:Record<string,string[]>={[A]:[C],[B]:[]};
  const writes:unknown[]=[];
  let failure=0;
  let delay=0;
  await page.route("**/api/**", async route=>{
    const req=route.request();const url=new URL(req.url());const path=url.pathname;
    if(path==="/api/households/"+H) return route.fulfill({json:{id:H,name:"Тестовая семья",members:[{id:A,name:"Анна",active:true},{id:B,name:"Борис",active:true}]}});
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
      return route.fulfill({json:{excluded_food_ingredient_ids:sets[member]}});
    }
    if(path==="/api/food-ingredients"){
      const q=url.searchParams.get("q")||"";
      if(q==="медленно") await new Promise(r=>setTimeout(r,600));
      const items=q==="медленно"?[foods[2]]:foods.filter(f=>f.is_active&&(f.canonical_name.toLowerCase().includes(q.toLowerCase())||(q==="мясо"&&f.id===D)));
      return route.fulfill({json:{items}});
    }
    const food=foods.find(f=>path.endsWith("/"+f.id));
    return route.fulfill(food?{json:food}:{status:404,json:{}});
  });
  await page.goto("/?household="+H);
  await expect(page.getByRole("heading",{name:"Не используем"})).toBeVisible();
  await expect(page.getByText("Морковь",{exact:true})).toBeVisible();
  return {sets,writes,fail:(s:number)=>{failure=s;},delay:(ms:number)=>{delay=ms;}};
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
  const f=await fixture(page);
  await page.getByRole("button",{name:"Удалить: Морковь"}).click();
  f.fail(code);
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByText("Не сохранено",{exact:true}).first()).toBeVisible();
  await expect(page.getByText(/Изменения сохранены/)).toHaveCount(0);
  expect(f.sets[A]).toEqual([C]);
  await expect(page.getByText("private",{exact:true})).toHaveCount(0);
});
test("save blocks switching and stale search does not win",async({page})=>{
  const f=await fixture(page);
  await page.getByRole("searchbox").fill("медленно");
  await page.waitForTimeout(350);
  await page.getByRole("searchbox").fill("говядина");
  await page.getByRole("button",{name:"Добавить: Говядина"}).click();
  await page.waitForTimeout(700);
  await expect(page.getByRole("button",{name:"Добавить: Свёкла"})).toHaveCount(0);
  f.delay(800);
  await page.getByRole("button",{name:"Сохранить",exact:true}).click();
  await expect(page.getByRole("button",{name:"Борис"})).toBeDisabled();
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
});
for(const width of [375,390,430,768,1024,1440])test("responsive "+width,async({page},info)=>{
  await page.setViewportSize({width,height:900});await fixture(page);
  await page.getByRole("searchbox").fill("говядина");
  await expect(page.getByRole("button",{name:"Добавить: Говядина"})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.getByRole("searchbox").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button",{name:"Добавить: Говядина"})).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button",{name:"Сохранить",exact:true})).toBeEnabled();
  await page.screenshot({path:info.outputPath("viewport-"+width+".png"),fullPage:true});
});
