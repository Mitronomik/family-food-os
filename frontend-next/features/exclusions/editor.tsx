"use client";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, type Food, type Household } from "./api";
import { MAX, add, remove, equal, sorted, reconcile, message, mustRefresh, displayName } from "./model.mjs";
type KnownFoods = Record<string, Food | undefined>;
type Draft = {
  base: string[];
  selected: string[];
  foods: KnownFoods;
  refresh: boolean;
  notice: string;
  saveFailed?: boolean;
};
type Review = { member: string; latest: string[]; foods: KnownFoods };
const unavailableAddition = (draft: Draft, id: string) =>
  !draft.base.includes(id) && !draft.foods[id]?.is_active;
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
  const [refreshing,setRefreshing]=useState(false);
  const saveGuard=useRef(false);
  const refreshGuard=useRef(false);
  const searchSeq=useRef(0);
  const draft=drafts[member];
  const dirty=Object.values(drafts).some(d=>!equal(d.base,d.selected)||d.refresh);
  const busy=Boolean(saving)||refreshing;
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
        [member]: { base: ids, selected: ids, foods, refresh: false, notice: "" },
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
      setDrafts(old=>({...old,[id]:{...old[id],base:confirmed,selected:confirmed,refresh:false,saveFailed:false,notice:"Изменения сохранены. Они будут учтены при следующей генерации меню."}}));
    }catch(e){
      const code=status(e);
      setDrafts(old=>({...old,[id]:{...old[id],refresh:mustRefresh(code),saveFailed:true,notice:message(code)}}));
    }finally{saveGuard.current=false;setSaving("");}
  }
  async function refresh(){
    if(!draft||saveGuard.current||refreshGuard.current)return;
    const id = member;
    refreshGuard.current = true;
    setRefreshing(true);
    setRefreshError("");
    try{
      const latest=sorted(await api.read(householdId,id));
      // Recheck pending additions too. A conflict can be caused by a product
      // becoming inactive while the draft was open, even with the same saved set.
      const additions = draft.selected.filter(foodId => !draft.base.includes(foodId));
      const foods = await resolveFoods(sorted([...latest, ...additions]));
      setReview({member:id,latest,foods});
    } catch (error) {
      setRefreshError(readFailure(error, "Участник не найден. Проверьте, доступен ли он для редактирования."));
    }
    finally{refreshGuard.current=false;setRefreshing(false);}
  }
  function acceptLatest(keep:boolean){
    if(!review||review.member!==member||!draft)return;
    const next=keep?reconcile(draft.base,draft.selected,review.latest):review.latest;
    update(d=>({...d,base:review.latest,selected:next,foods:{...d.foods,...review.foods},refresh:false,saveFailed:false,notice:"Проверьте актуальный выбор перед сохранением."}));
    changeQuery("");
    setReview(undefined);
  }
  const current=family?.members.find(m=>m.id===member);
  const memberError = memberRead?.member === member ? memberRead.message : "";
  const editable=Boolean(draft&&current?.active&&!busy&&!review);
  const hasUnavailable = Boolean(draft?.selected.some(id => unavailableAddition(draft, id)));
  const overLimit = (draft?.selected.length ?? 0) > MAX;
  const canSave = Boolean(editable && draft && !draft.refresh && !hasUnavailable
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
          {draft.selected.length===0?<p className="muted">Нет исключённых продуктов. Добавьте нужные через поиск.</p>:<ul>{draft.selected.map(id=><li key={id}><div><strong>{displayName(draft.foods[id])}</strong>{unavailableAddition(draft, id) ? <small>Нельзя добавить в исключения</small>
            : draft.foods[id]?.is_active === false ? <small>Больше не в каталоге · исключение сохранено</small>
            : !draft.foods[id] ? <small>Не удалось получить сведения о продукте</small> : null}</div><button disabled={!editable} aria-label={"Удалить: "+displayName(draft.foods[id])} onClick={()=>update(d=>({...d,selected:remove(d.selected,id),notice:d.refresh?d.notice:"",saveFailed:d.refresh}))}>Удалить</button></li>)}</ul>}
        </section><section className="search"><h3>Добавить продукт</h3><label htmlFor="food-search">Название продукта</label><input id="food-search" type="search" value={query} maxLength={240} disabled={!editable} placeholder="Например, морковь" onChange={event => changeQuery(event.target.value)}/>
          {searchState==="idle"?<p className="muted">Введите название или синоним.</p>:searchState==="loading"?<p role="status">Ищем продукты…</p>:searchState==="error"?<p role="alert">Не удалось выполнить поиск. Измените запрос и попробуйте снова.</p>:results.length===0?<p role="status">Ничего не найдено. Попробуйте другое название.</p>:<ul>{results.map(food=><li key={food.id}><span>{displayName(food)}</span><button disabled={!editable||!food.is_active||draft.selected.includes(food.id)||draft.selected.length>=MAX||displayName(food)==="Название недоступно"} aria-label={"Добавить: "+displayName(food)} onClick={()=>update(d=>({...d,selected:add(d.selected,food),foods:{...d.foods,[food.id]:food},notice:d.refresh?d.notice:"",saveFailed:d.refresh}))}>{draft.selected.includes(food.id)?"Добавлено":"Добавить"}</button></li>)}</ul>}
        </section></div>
        {draft.notice?<p role={draft.saveFailed?"alert":"status"} className={draft.saveFailed?"alert":"notice"}>{draft.notice}</p>:null}
        {refreshError ? <p role="alert" className="alert">{refreshError}</p> : null}
        {refreshing ? <p role="status">Обновляем список…</p> : null}
        {hasUnavailable ? <p role="status">Удалите недоступные продукты, чтобы сохранить выбор.</p> : null}
        {overLimit ? <p role="status">Сократите список до {MAX} продуктов, чтобы сохранить выбор.</p> : null}
        {draft.refresh?<button disabled={busy||Boolean(review)} onClick={refresh}>Обновить актуальный список</button>:null}
        {review?.member===member?<section className="review" aria-label="Проверка актуального списка"><h3>Актуальные исключения</h3>{review.latest.length ? <ul>{review.latest.map(id => <li key={id}>{displayName(review.foods[id])}</li>)}</ul> : <p>Сохранённых исключений нет.</p>}<p>Можно перенести ваши изменения в актуальный список или оставить только сохранённый выбор. Запись произойдёт только после отдельного сохранения.</p><button onClick={()=>acceptLatest(true)}>Перенести мои изменения</button> <button onClick={()=>acceptLatest(false)}>Оставить актуальный список</button></section>:null}
        <footer className="save"><p className="muted">Изменения действуют при следующей генерации меню. Уже составленная неделя не изменится.</p><button className="primary" disabled={!canSave} onClick={save}>{saving?"Сохраняем…":"Сохранить"}</button></footer>
        </>:null}
      </section>:null}
    </div>:null}
  </main>;
}
async function resolveFoods(ids: string[], signal?: AbortSignal): Promise<KnownFoods> {
  const entries=await Promise.all(ids.map(async id=>{
    try{return [id,await api.food(id,signal)] as const;}catch{return [id,undefined] as const;}
  }));
  return Object.fromEntries(entries);
}
