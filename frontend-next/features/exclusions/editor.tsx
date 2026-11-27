"use client";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, type Food, type Household } from "./api";
import { MAX, add, remove, equal, sorted, reconcile, message, mustRefresh, describeFood } from "./model.mjs";
type KnownFoods = Record<string, Food | undefined>;
type Draft = {
  base: string[];
  selected: string[];
  foods: KnownFoods;
  recovery?: "selection" | "member";
  notice: string;
  saveFailed?: boolean;
};
type Review = { member: string; latest: string[]; foods: KnownFoods };
const unavailableAddition = (draft: Draft, id: string) =>
  !draft.base.includes(id) &&
  (!draft.foods[id]?.is_active || describeFood(draft.foods[id]).kind !== "identified");
const status = (error: unknown) => error instanceof ApiError ? error.status : 0;

function readFailure(error: unknown, missing: string) {
  const code = status(error);
  if (code === 404) return missing;
  if (code >= 500) return "Загрузка временно недоступна. Попробуйте ещё раз.";
  if (code === 422) return "Не удалось загрузить данные для этого выбора.";
  return message(code);
}
export default function Editor({householdId}:{householdId:string}) {
  const [family,setFamily]=useState<Household>();
  const [member,setMember]=useState("");
  const [drafts,setDrafts]=useState<Record<string,Draft>>({});
  const [familyError, setFamilyError] = useState("");
  const [memberRead, setMemberRead] = useState<{ member: string; message: string }>();
  const [saving,setSaving]=useState("");
  const [refreshError, setRefreshError] = useState("");
  const [query,setQuery]=useState("");
  const [results,setResults]=useState<Food[]>([]);
  const [searchState,setSearchState]=useState("idle");
  const [retry,setRetry]=useState(0);
  const [familyRetry,setFamilyRetry]=useState(0);
  const [review, setReview] = useState<Review>();
  const [refreshing, setRefreshing] = useState<"selection" | "metadata">();
  const [metadataNotice, setMetadataNotice] = useState("");
  const saveGuard=useRef(false);
  const refreshGuard=useRef(false);
  const searchSeq=useRef(0);
  const draft=drafts[member];
  const dirty=Object.values(drafts).some(d=>!equal(d.base,d.selected)||d.recovery);
  const busy = Boolean(saving || refreshing);
  useEffect(()=>{
    if(!householdId)return;
    const abort=new AbortController();
    api.household(householdId, abort.signal).then(result => {
      if (abort.signal.aborted) return;
      setFamily(result);
      setMember(result.members.find(item => item.active)?.id ?? result.members[0]?.id ?? "");
    }).catch(error => {
      if (!abort.signal.aborted) setFamilyError(readFailure(error, "Семья не найдена. Проверьте ссылку."));
    });
    return () => abort.abort();
  }, [householdId, familyRetry]);

  useEffect(() => {
    if (!member || draft) return;
    const abort = new AbortController();
    (async () => {
      const ids = sorted(await api.read(householdId, member, abort.signal));
      if (abort.signal.aborted) return;
      const foods = await resolveFoods(ids, abort.signal);
      if (abort.signal.aborted) return;
      setDrafts(previous => ({
        ...previous,
        [member]: { base: ids, selected: ids, foods, notice: "" },
      }));
    })().catch(error => {
      if (!abort.signal.aborted) setMemberRead({ member, message: readFailure(error, "Участник не найден. Повторите загрузку или выберите другого участника.") });
    });
    return () => abort.abort();
  }, [householdId, member, retry, draft]);

  useEffect(()=>{
    const seq=++searchSeq.current;
    const abort=new AbortController();
    setResults([]);
    if(!member||!query.trim()){setSearchState("idle");return;}
    setSearchState("loading");
    const timer=setTimeout(()=>{
      api.search(query.trim(),abort.signal).then(items=>{
        if(seq!==searchSeq.current||abort.signal.aborted)return;
        setResults(items);setSearchState("ready");
      }).catch(()=>{if(seq===searchSeq.current&&!abort.signal.aborted)setSearchState("error");});
    },300);
    return ()=>{clearTimeout(timer);abort.abort();};
  },[query,member]);
  useEffect(()=>{
    if(!dirty&&!busy)return;
    const guard=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue="";};
    window.addEventListener("beforeunload",guard);
    return ()=>window.removeEventListener("beforeunload",guard);
  },[dirty,busy]);
  function changeQuery(value: string) {
    searchSeq.current++;
    setResults([]);
    setSearchState(value.trim() ? "loading" : "idle");
    setQuery(value);
  }

  function choose(id:string){
    if(saveGuard.current||refreshGuard.current||id===member)return;
    changeQuery("");
    setMemberRead(undefined);
    setRefreshError("");
    setMetadataNotice("");
    setReview(undefined);
    setMember(id);
  }
  function update(fn:(d:Draft)=>Draft) {
    if(saveGuard.current||refreshGuard.current)return;
    setDrafts(old=>old[member]?{...old,[member]:fn(old[member])}:old);
  }
  async function save(){
    if (!canSave || !draft || saveGuard.current || refreshGuard.current) return;
    const id = member;
    saveGuard.current = true;
    setSaving(id);
    setRefreshError("");
    try{
      const res=await api.save(householdId,id,draft.base,draft.selected);
      const confirmed=sorted(res.excluded_food_ingredient_ids);
      setDrafts(old=>({...old,[id]:{...old[id],base:confirmed,selected:confirmed,recovery:undefined,saveFailed:false,notice:"Изменения сохранены. Они будут учтены при следующей генерации меню."}}));
    }catch(e){
      const code=status(e);
      const recovery = code === 422 ? "member" : mustRefresh(code) ? "selection" : undefined;
      const notice = code === 0
        ? "Не удалось связаться с сервисом. Обновите список, чтобы проверить сохранение."
        : code === 422
          ? "Не удалось проверить выбор. Сначала проверьте статус участника."
          : message(code);
      setDrafts(old => ({ ...old, [id]: { ...old[id], recovery, saveFailed: true, notice } }));
      if (recovery === "member") await refreshMemberStatus(id);
    }finally{saveGuard.current=false;setSaving("");}
  }
  async function refreshMemberStatus(id: string) {
    try {
      const updated = await api.household(householdId);
      const participant = updated.members.find(item => item.id === id);
      if (!participant) throw new ApiError(404);
      setFamily(updated);
      const notice = participant.active
        ? message(422)
        : "Участник стал неактивным. Черновик сохранён в этой вкладке.";
      setDrafts(old => ({
        ...old, [id]: { ...old[id], recovery: undefined, notice },
      }));
    } catch (error) {
      setRefreshError(readFailure(error, "Участник не найден. Выберите другого участника."));
    }
  }

  async function refresh(){
    if (!draft?.recovery || saveGuard.current || refreshGuard.current) return;
    const id = member;
    refreshGuard.current = true;
    setRefreshing("selection");
    setRefreshError("");
    try{
      if (draft.recovery === "member") {
        await refreshMemberStatus(id);
        return;
      }
      const latest=sorted(await api.read(householdId,id));
      // Recheck pending additions too. A conflict can be caused by a product
      // becoming inactive while the draft was open, even with the same saved set.
      const additions = draft.selected.filter(foodId => !draft.base.includes(foodId));
      const foods = await resolveFoods(sorted([...latest, ...additions]));
      setReview({member:id,latest,foods});
    } catch (error) {
      setRefreshError(readFailure(error, "Участник не найден. Проверьте, доступен ли он для редактирования."));
    }
    finally{refreshGuard.current=false;setRefreshing(undefined);}
  }
  function acceptLatest(keep:boolean){
    if(!review||review.member!==member||!draft)return;
    const next=keep?reconcile(draft.base,draft.selected,review.latest):review.latest;
    const notice = equal(next, review.latest)
      ? "Выбор совпадает с сохранённым списком."
      : "Проверьте актуальный выбор перед сохранением.";
    update(d => ({
      ...d, base: review.latest, selected: next, foods: { ...d.foods, ...review.foods },
      recovery: undefined, saveFailed: false, notice,
    }));
    changeQuery("");
    setMetadataNotice("");
    setReview(undefined);
  }

  async function retryMetadata() {
    if (!draft || draft.recovery || !unresolved.length || saveGuard.current || refreshGuard.current) return;
    refreshGuard.current = true;
    setRefreshing("metadata");
    setMetadataNotice("");
    try {
      const foods = await resolveFoods(unresolved);
      setDrafts(old => ({
        ...old, [member]: { ...old[member], foods: { ...old[member].foods, ...foods } },
      }));
      const restored = unresolved.filter(id => describeFood(foods[id]).kind === "identified").length;
      setMetadataNotice(restored === unresolved.length
        ? "Сведения о продуктах обновлены."
        : restored > 0 ? "Сведения о продуктах обновлены частично." : "Уточнить продукты пока не удалось.");
    } finally {
      refreshGuard.current = false;
      setRefreshing(undefined);
    }
  }

  const current=family?.members.find(m=>m.id===member);
  const memberError = memberRead?.member === member ? memberRead.message : "";
  const editable = Boolean(draft && current?.active && !busy && !draft.recovery);
  const unresolved = draft?.selected.filter(id => describeFood(draft.foods[id]).kind !== "identified") ?? [];
  const unknownAdditions = unresolved.filter(id => !draft?.base.includes(id));
  const hasUnavailable = Boolean(draft?.selected.some(id => unavailableAddition(draft, id)));
  const overLimit = (draft?.selected.length ?? 0) > MAX;
  const canSave = Boolean(editable && draft && !hasUnavailable
    && !overLimit && !equal(draft.base, draft.selected));
  return <main className="shell">
    <header className="top"><span className="brand">FF</span><span>FamilyFoodOS</span><span className="internal">Внутренняя версия</span></header>
    <div className="intro"><p className="eyebrow">Настройки питания</p><h1>Семья</h1><p>Настройте продукты отдельно для каждого участника.</p></div>
    {!householdId?<section className="panel"><h2>Семья не выбрана</h2><p>Откройте ссылку на тестовую семью, предоставленную разработчиком.</p></section>:null}
    {householdId && !family && !familyError ? <p role="status">Загружаем семью…</p> : null}
    {familyError ? <div className="alert"><p role="alert">{familyError}</p><button onClick={() => {
      setFamilyError("");
      setFamilyRetry(value => value + 1);
    }}>Повторить загрузку семьи</button></div> : null}
    {family?<div className="workspace">
      <aside className="panel members"><h2>{family.name}</h2><p className="muted">Участники</p>
        {family.members.length===0?<p>В семье пока нет участников.</p>:family.members.map(m=><button key={m.id} className="member" aria-pressed={m.id===member} disabled={busy} onClick={()=>choose(m.id)}>
          <span>{m.name}{!m.active?" · Неактивен":""}</span><small>{drafts[m.id]&&!equal(drafts[m.id].base,drafts[m.id].selected)?"Не сохранено":""}</small>
        </button>)}
      </aside>
      {current?<section className="panel editor"><div className="heading"><div><p className="eyebrow">{current.name}</p><h2>Не используем</h2></div>{draft&&!equal(draft.base,draft.selected)?<span className="pending">Не сохранено</span>:null}</div>
        <p>Выберите продукты, которые не нужно добавлять в блюда для этого участника семьи.</p>
        {!current.active?<p role="status">Участник неактивен. Исключения доступны только для просмотра.</p>:null}
        {!draft && !memberError ? <p role="status">Загружаем исключения…</p> : null}
        {memberError ? <div className="alert"><p role="alert">{memberError}</p><button onClick={() => {
          setMemberRead(undefined);
          setRetry(value => value + 1);
        }}>Повторить загрузку исключений</button></div> : null}
        {draft?<><div className="columns"><section className="selected" aria-labelledby="selected-food-heading"><h3 id="selected-food-heading">Выбрано · {draft.selected.length}</h3>
          {draft.selected.length === 0
            ? <p className="muted">Нет исключённых продуктов. Добавьте нужные через поиск.</p>
            : <ul>{draft.selected.map(id => {
              const food = draft.foods[id];
              const identity = describeFood(food);
              return <li key={id}>
                <div>
                  <strong>{identity.label}</strong>
                  {identity.kind !== "identified"
                    ? <small>{draft.base.includes(id) ? "Сохранённое исключение" : "Новое добавление"} · удаление доступно после уточнения</small>
                    : unavailableAddition(draft, id) ? <small>Нельзя добавить в исключения</small>
                    : food?.is_active === false ? <small>Больше не в каталоге · исключение сохранено</small> : null}
                </div>
                <button disabled={!editable || identity.kind !== "identified"} aria-label={"Удалить: " + identity.label}
                  onClick={() => update(d => ({ ...d, selected: remove(d.selected, id, d.foods[id]), notice: "", saveFailed: false }))}>
                  Удалить
                </button>
              </li>;
            })}</ul>}
          {unresolved.length > 0
            ? <button disabled={busy || Boolean(draft.recovery)} onClick={retryMetadata}>Повторить загрузку сведений</button>
            : null}
          {refreshing === "metadata"
            ? <p role="status">Загружаем сведения о продуктах…</p>
            : metadataNotice ? <p role="status">{metadataNotice}</p> : null}
        </section><section className="search"><h3>Добавить продукт</h3><label htmlFor="food-search">Название продукта</label><input id="food-search" type="search" value={query} maxLength={240} disabled={!editable} placeholder="Например, морковь" onChange={event => changeQuery(event.target.value)}/>
          {searchState === "idle" ? <p className="muted">Введите название или синоним.</p>
            : searchState === "loading" ? <p role="status">Ищем продукты…</p>
            : searchState === "error" ? <p role="alert">Не удалось выполнить поиск. Измените запрос и попробуйте снова.</p>
            : results.length === 0 ? <p role="status">Ничего не найдено. Попробуйте другое название.</p>
            : <ul>{results.map(food => {
              const identity = describeFood(food);
              const selected = draft.selected.includes(food.id);
              return <li key={food.id}>
                <span>{identity.label}</span>
                <button disabled={!editable || !food.is_active || selected || draft.selected.length >= MAX || identity.kind !== "identified"}
                  aria-label={"Добавить: " + identity.label}
                  onClick={() => update(d => ({
                    ...d, selected: add(d.selected, food), foods: { ...d.foods, [food.id]: food }, notice: "", saveFailed: false,
                  }))}>
                  {selected ? "Добавлено" : "Добавить"}
                </button>
              </li>;
            })}</ul>}
        </section></div>
        {draft.notice?<p role={draft.saveFailed?"alert":"status"} className={draft.saveFailed?"alert":"notice"}>{draft.notice}</p>:null}
        {refreshError ? <p role="alert" className="alert">{refreshError}</p> : null}
        {refreshing === "selection" ? <p role="status">{draft.recovery === "member" ? "Проверяем статус участника…" : "Обновляем список…"}</p> : null}
        {hasUnavailable ? <p role="status">Чтобы сохранить выбор, уточните или отмените недоступные добавления.</p> : null}
        {unknownAdditions.length > 0 ? <button disabled={!editable} onClick={() => update(d => ({
          ...d, selected: d.selected.filter(id => !unknownAdditions.includes(id)), notice: "", saveFailed: false,
        }))}>Отменить неуточнённые добавления</button> : null}
        {overLimit ? <p role="status">Сократите список до {MAX} продуктов, чтобы сохранить выбор.</p> : null}
        {draft.recovery ? <button disabled={busy || Boolean(review)} onClick={refresh}>
          {draft.recovery === "member" ? "Проверить статус участника" : "Обновить актуальный список"}
        </button> : null}
        {review?.member===member?<section className="review" aria-label="Проверка актуального списка"><h3>Актуальные исключения</h3>{review.latest.length ? <ul>{review.latest.map(id => <li key={id}>{describeFood(review.foods[id]).label}</li>)}</ul> : <p>Сохранённых исключений нет.</p>}<p>Можно перенести ваши изменения в актуальный список или оставить только сохранённый выбор. Запись произойдёт только после отдельного сохранения.</p><button onClick={()=>acceptLatest(true)}>Перенести мои изменения</button> <button onClick={()=>acceptLatest(false)}>Оставить актуальный список</button></section>:null}
        <footer className="save"><p className="muted">Изменения действуют при следующей генерации меню. Уже составленная неделя не изменится.</p><button className="primary" disabled={!canSave} onClick={save}>{saving?"Сохраняем…":"Сохранить"}</button></footer>
        </>:null}
      </section>:null}
    </div>:null}
  </main>;
}
async function resolveFoods(ids: string[], signal?: AbortSignal): Promise<KnownFoods> {
  const entries=await Promise.all(ids.map(async id=>{
    try {
      const food = await api.food(id, signal);
      return [id, food?.id === id ? food : undefined] as const;
    } catch {
      // Keep the selection by ID even if its catalogue details cannot be read.
      return [id, undefined] as const;
    }
  }));
  return Object.fromEntries(entries);
}
