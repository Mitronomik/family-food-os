"use client";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, type Food, type Household } from "./api";
import { MAX, add, remove, equal, sorted, reconcile, message, mustRefresh, displayName } from "./model.mjs";
type Draft = { base:string[]; selected:string[]; foods:Record<string,Food>; refresh:boolean; notice:string };
const status = (error:unknown) => error instanceof ApiError ? error.status : 0;
export default function Editor({householdId}:{householdId:string}) {
  const [family,setFamily]=useState<Household>();
  const [member,setMember]=useState("");
  const [drafts,setDrafts]=useState<Record<string,Draft>>({});
  const [loading,setLoading]=useState(false);
  const [saving,setSaving]=useState("");
  const [error,setError]=useState("");
  const [query,setQuery]=useState("");
  const [results,setResults]=useState<Food[]>([]);
  const [searchState,setSearchState]=useState("idle");
  const [retry,setRetry]=useState(0);
  const [familyRetry,setFamilyRetry]=useState(0);
  const [review,setReview]=useState<{member:string;latest:string[];foods:Record<string,Food>}>();
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
    setFamily(undefined);setMember("");setDrafts({});setError("");setLoading(true);
    api.household(householdId,abort.signal).then(f=>{
      if(abort.signal.aborted)return;
      setFamily(f);setMember(f.members.find(m=>m.active)?.id||f.members[0]?.id||"");
    }).catch(e=>{if(!abort.signal.aborted)setError(message(status(e)));})
      .finally(()=>{if(!abort.signal.aborted)setLoading(false);});
    return ()=>abort.abort();
  },[householdId,familyRetry]);
  useEffect(()=>{
    if(!member||drafts[member])return;
    const abort=new AbortController();
    setError("");setLoading(true);
    (async()=>{
      const ids=await api.read(householdId,member,abort.signal);
      const foods=await resolveFoods(ids,abort.signal);
      if(!abort.signal.aborted)setDrafts(old=>({...old,[member]:{base:sorted(ids),selected:sorted(ids),foods,refresh:false,notice:""}}));
    })().catch(e=>{if(!abort.signal.aborted)setError(message(status(e)));})
      .finally(()=>{if(!abort.signal.aborted)setLoading(false);});
    return ()=>abort.abort();
    // An existing member draft is deliberately retained in memory.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[householdId,member,retry]);
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
  function choose(id:string){
    if(saveGuard.current||refreshGuard.current||id===member)return;
    searchSeq.current++;setQuery("");setResults([]);setSearchState("idle");
    setError("");setReview(undefined);setLoading(false);setMember(id);
  }
  function update(fn:(d:Draft)=>Draft) {
    if(saveGuard.current||refreshGuard.current)return;
    setDrafts(old=>old[member]?{...old,[member]:fn(old[member])}:old);
  }
  async function save(){
    if(!draft||draft.refresh||equal(draft.base,draft.selected)||saveGuard.current||refreshGuard.current)return;
    const id=member;saveGuard.current=true;setSaving(id);setError("");
    try{
      const res=await api.save(householdId,id,draft.base,draft.selected);
      const confirmed=sorted(res.excluded_food_ingredient_ids);
      setDrafts(old=>({...old,[id]:{...old[id],base:confirmed,selected:confirmed,refresh:false,notice:"Изменения сохранены. Они будут учтены при следующей генерации меню."}}));
    }catch(e){
      const code=status(e);
      setDrafts(old=>({...old,[id]:{...old[id],refresh:mustRefresh(code),notice:message(code)}}));
    }finally{saveGuard.current=false;setSaving("");}
  }
  async function refresh(){
    if(!draft||saveGuard.current||refreshGuard.current)return;
    const id=member;refreshGuard.current=true;setRefreshing(true);setError("");
    try{
      const latest=sorted(await api.read(householdId,id));
      const foods=await resolveFoods(latest);
      setReview({member:id,latest,foods});
    }catch(e){setError(message(status(e)));}
    finally{refreshGuard.current=false;setRefreshing(false);}
  }
  function acceptLatest(keep:boolean){
    if(!review||review.member!==member||!draft)return;
    const next=keep?reconcile(draft.base,draft.selected,review.latest):review.latest;
    if(next.length>MAX){setError("Слишком много продуктов. Сохраните не более 128 исключений.");return;}
    update(d=>({...d,base:review.latest,selected:next,foods:{...d.foods,...review.foods},refresh:false,notice:"Проверьте актуальный выбор перед сохранением."}));
    setReview(undefined);
  }
  const current=family?.members.find(m=>m.id===member);
  const editable=Boolean(draft&&current?.active&&!busy&&!review);
  const canSave=editable&&draft&&!draft.refresh&&!equal(draft.base,draft.selected);
  return <main className="shell">
    <header className="top"><span className="brand">FF</span><span>FamilyFoodOS</span><span className="internal">Внутренняя версия</span></header>
    <div className="intro"><p className="eyebrow">Настройки питания</p><h1>Семья</h1><p>Настройте продукты отдельно для каждого участника.</p></div>
    {!householdId?<section className="panel"><h2>Семья не выбрана</h2><p>Откройте ссылку на тестовую семью, предоставленную разработчиком.</p></section>:null}
    {!family&&loading?<p role="status">Загружаем семью…</p>:null}
    {error?<div role="alert" className="alert">{error} <button onClick={()=>family?setRetry(x=>x+1):setFamilyRetry(x=>x+1)}>Повторить</button></div>:null}
    {family?<div className="workspace">
      <aside className="panel members"><h2>{family.name}</h2><p className="muted">Участники</p>
        {family.members.length===0?<p>В семье пока нет участников.</p>:family.members.map(m=><button key={m.id} className="member" aria-pressed={m.id===member} disabled={busy} onClick={()=>choose(m.id)}>
          <span>{m.name}{!m.active?" · Неактивен":""}</span><small>{drafts[m.id]&&!equal(drafts[m.id].base,drafts[m.id].selected)?"Не сохранено":""}</small>
        </button>)}
      </aside>
      {current?<section className="panel editor"><div className="heading"><div><p className="eyebrow">{current.name}</p><h2>Не используем</h2></div>{draft&&!equal(draft.base,draft.selected)?<span className="pending">Не сохранено</span>:null}</div>
        <p>Выберите продукты, которые не нужно добавлять в блюда для этого участника семьи.</p>
        {!current.active?<p role="status">Участник неактивен. Исключения доступны только для просмотра.</p>:null}
        {loading&&!draft?<p role="status">Загружаем исключения…</p>:null}
        {draft?<><div className="columns"><section className="selected"><h3>Выбрано · {draft.selected.length}</h3>
          {draft.selected.length===0?<p className="muted">Нет исключённых продуктов. Добавьте нужные через поиск.</p>:<ul>{draft.selected.map(id=><li key={id}><div><strong>{displayName(draft.foods[id])}</strong>{draft.foods[id]?.is_active===false?<small>Больше не в каталоге · исключение сохранено</small>:!draft.foods[id]?<small>Не удалось получить сведения о продукте</small>:null}</div><button disabled={!editable} aria-label={"Удалить: "+displayName(draft.foods[id])} onClick={()=>update(d=>({...d,selected:remove(d.selected,id),notice:""}))}>Удалить</button></li>)}</ul>}
        </section><section className="search"><h3>Добавить продукт</h3><label htmlFor="food-search">Название продукта</label><input id="food-search" type="search" value={query} maxLength={240} disabled={!editable} placeholder="Например, морковь" onChange={e=>{searchSeq.current++;setResults([]);setQuery(e.target.value);}}/>
          {searchState==="idle"?<p className="muted">Введите название или синоним.</p>:searchState==="loading"?<p role="status">Ищем продукты…</p>:searchState==="error"?<p role="alert">Не удалось выполнить поиск. Измените запрос и попробуйте снова.</p>:results.length===0?<p role="status">Ничего не найдено. Попробуйте другое название.</p>:<ul>{results.map(food=><li key={food.id}><span>{displayName(food)}</span><button disabled={!editable||!food.is_active||draft.selected.includes(food.id)||draft.selected.length>=MAX||displayName(food)==="Название недоступно"} aria-label={"Добавить: "+displayName(food)} onClick={()=>update(d=>({...d,selected:add(d.selected,food),foods:{...d.foods,[food.id]:food},notice:""}))}>{draft.selected.includes(food.id)?"Добавлено":"Добавить"}</button></li>)}</ul>}
        </section></div>
        {draft.notice?<p role={draft.refresh?"alert":"status"} className="notice">{draft.notice}</p>:null}
        {draft.refresh?<button disabled={busy||Boolean(review)} onClick={refresh}>Обновить актуальный список</button>:null}
        {review?.member===member?<section className="review" aria-label="Проверка актуального списка"><h3>Актуальные исключения</h3><ul>{review.latest.map(id=><li key={id}>{displayName(review.foods[id])}</li>)}</ul><p>Можно перенести ваши изменения в актуальный список или оставить только сохранённый выбор. Запись произойдёт только после отдельного сохранения.</p><button onClick={()=>acceptLatest(true)}>Перенести мои изменения</button> <button onClick={()=>acceptLatest(false)}>Оставить актуальный список</button></section>:null}
        <footer className="save"><p className="muted">Изменения действуют при следующей генерации меню. Уже составленная неделя не изменится.</p><button className="primary" disabled={!canSave} onClick={save}>{saving?"Сохраняем…":"Сохранить"}</button></footer>
        </>:null}
      </section>:null}
    </div>:null}
  </main>;
}
async function resolveFoods(ids:string[],signal?:AbortSignal){
  const entries=await Promise.all(ids.map(async id=>{
    try{return [id,await api.food(id,signal)] as const;}catch{return [id,undefined] as const;}
  }));
  return Object.fromEntries(entries.filter((entry):entry is readonly [string,Food]=>Boolean(entry[1])));
}
