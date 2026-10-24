// Home Assistant mounts this custom element as a full-page panel and supplies
// its authenticated object for calling the integration WebSocket API.
class RollingMealplanPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._loaded = false;
    this._message = "";
    this._weekStart = this._monday();
    this._data = {meals:[],schedule:Array(84).fill(null),anchor_date:"",weeks:12};
  }
  set hass(value) {
    this._hass = value;
    if (!this._loaded && value) { this._loaded = true; this._load(); }
  }
  get hass() { return this._hass; }
  // Start the view at the current Monday; users can browse either direction.
  _monday() {
    const d = new Date(); d.setHours(0,0,0,0);
    d.setDate(d.getDate()-((d.getDay()+6)%7)); return d;
  }
  // Keep all frontend requests on the authenticated Home Assistant WebSocket.
  _api(type, fields={}) {
    return this._hass.connection.sendMessagePromise({type:"rolling_mealplan/"+type,...fields});
  }
  async _load() {
    try { this._data = await this._api("get"); this._render(); }
    catch (err) { this._message = "Laden fehlgeschlagen: "+(err.message||err); this._render(); }
  }
  _dateAt(offset) { const d=new Date(this._weekStart); d.setDate(d.getDate()+offset); return d; }
  _slot(date) {
    const anchor=new Date(this._data.anchor_date+"T00:00:00"); const d=new Date(date); d.setHours(0,0,0,0);
    // Navigation can span past and future weeks; assignments wrap through the currently configured cycle.
    const cycleDays=this._data.schedule.length||84;
    return ((Math.round((d-anchor)/86400000)%cycleDays)+cycleDays)%cycleDays;
  }
  _fmt(d, opts={weekday:"long",day:"2-digit",month:"2-digit"}) {
    return new Intl.DateTimeFormat(this._hass?.locale?.language||"de-DE",opts).format(d);
  }
  _esc(s) {
    return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }
  // Build the week cards from the selected dates and the matching cycle slots.
  _render() {
    const meals=this._data.meals||[], sunday=this._dateAt(6), now=new Date(); now.setHours(0,0,0,0);
    const range=this._fmt(this._weekStart,{day:"2-digit",month:"long",year:"numeric"})+" – "+this._fmt(sunday,{day:"2-digit",month:"long",year:"numeric"});
    const planWeek=Math.floor(this._slot(this._weekStart)/7)+1;
    const rows=Array.from({length:7},(_,i)=>{
      const date=this._dateAt(i),slot=this._slot(date),id=this._data.schedule[slot]||"",meal=meals.find(m=>m.id===id);
      const options=['<option value="">— Gericht wählen —</option>'].concat(meals.map(m=>'<option value="'+this._esc(m.id)+'"'+(m.id===id?" selected":"")+'>'+this._esc(m.name)+'</option>')).join("");
      const today=date.getTime()===now.getTime();
      return '<article class="day '+(today?"today":"")+'"><div class="dayname"><b>'+this._esc(this._fmt(date))+'</b>'+(today?'<span>Heute</span>':"")+'<small>'+this._esc(this._fmt(date,{day:"2-digit",month:"2-digit"}))+'</small></div>'+
        '<select data-slot="'+slot+'">'+options+'</select>'+
        (meal?'<small class="ingredients">'+this._esc((meal.ingredients||[]).join(", ")||"Keine Zutaten")+'</small>':'')+
        '<button class="secondary shop" data-shop="'+slot+'"'+(!meal?" disabled":"")+'>Zutaten zur Einkaufsliste</button></article>';
    }).join("");
    const library=meals.length?meals.map(m=>'<li><span><b>'+this._esc(m.name)+'</b><small>'+this._esc((m.ingredients||[]).join(", ")||"Keine Zutaten")+'</small></span><span><button class="secondary edit" data-edit="'+this._esc(m.id)+'">Ändern</button> <button class="danger delete" data-delete="'+this._esc(m.id)+'">Löschen</button></span></li>').join(""):'<li class="muted">Noch keine Gerichte angelegt.</li>';
    const css=":host{display:block;color:var(--primary-text-color);background:var(--primary-background-color);min-height:100%;font-family:Arial,sans-serif}*{box-sizing:border-box}main{max-width:1100px;margin:auto;padding:24px}header,.head{display:flex;align-items:center;justify-content:space-between;gap:16px}h1{font-size:32px;margin:0}.eyebrow,.muted,.range,.foot{color:var(--secondary-text-color)}.eyebrow{font-size:12px;text-transform:uppercase;margin:0 0 5px}.range{margin:6px 0}nav{display:flex;gap:8px}button,.import{font:inherit;border:0;border-radius:8px;padding:10px 14px;cursor:pointer}.primary{background:var(--primary-color);color:white}.secondary,.import{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color)}.danger{background:transparent;color:var(--error-color);border:1px solid var(--divider-color)}button:disabled{opacity:.5;cursor:not-allowed}.days{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:24px 0}.day{display:grid;grid-template-columns:125px 1fr;align-items:center;gap:8px 12px;padding:15px;border:1px solid var(--divider-color);border-radius:12px;background:var(--card-background-color,var(--secondary-background-color))}.today{border-color:var(--primary-color);box-shadow:inset 3px 0 var(--primary-color)}.dayname{display:flex;flex-wrap:wrap;gap:5px;align-items:center}.dayname span{background:var(--primary-color);color:white;border-radius:10px;padding:2px 7px;font-size:11px}.dayname small{width:100%}select,input,textarea{font:inherit;color:var(--primary-text-color);background:var(--card-background-color,var(--primary-background-color));border:1px solid var(--divider-color);border-radius:7px;padding:9px;width:100%}.ingredients,.shop{grid-column:2}.shop{justify-self:start}.manage{padding:20px;border:1px solid var(--divider-color);border-radius:12px;background:var(--card-background-color,var(--secondary-background-color))}.head p{margin:4px 0}ul{list-style:none;padding:0;margin:16px 0}li{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--divider-color)}li span:first-child{display:grid;gap:4px}li button{padding:6px 9px;font-size:13px}.transfer{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:15px}.transfer p{flex-basis:100%;margin:0}.import{position:relative;overflow:hidden;display:inline-block}.import input{position:absolute;inset:0;opacity:0;cursor:pointer}.msg{padding:10px;background:var(--secondary-background-color);border-radius:8px}.foot{margin-top:14px}dialog{color:var(--primary-text-color);background:var(--card-background-color,var(--primary-background-color));border:1px solid var(--divider-color);border-radius:12px;width:min(480px,90vw)}dialog::backdrop{background:#0008}.form{display:grid;gap:12px}.form label{display:grid;gap:6px}.actions{display:flex;justify-content:flex-end;gap:8px}@media(max-width:700px){main{padding:16px}.days{grid-template-columns:1fr}header{align-items:flex-start;flex-direction:column}.day{grid-template-columns:1fr}.ingredients,.shop{grid-column:1}li{align-items:flex-start;flex-direction:column}}";
    this.shadowRoot.innerHTML="<style>"+css+"</style><main><header><div><p class='eyebrow'>Familien-Speiseplan</p><h1>Woche "+planWeek+"</h1><p class='range'>"+this._esc(range)+"</p></div><nav><button class='secondary prev' aria-label='Vorherige Woche'>‹</button><button class='secondary current'>Diese Woche</button><button class='secondary next' aria-label='Nächste Woche'>›</button></nav></header>"+
      (this._message?'<p class="msg">'+this._esc(this._message)+'</p>':"")+'<section class="days">'+rows+'</section><section class="manage"><div class="head"><div><h2>Gerichte</h2><p class="muted">Gerichte mit einfacher Zutatenliste.</p></div><button class="primary add">Gericht hinzufügen</button></div><ul>'+library+'</ul><div class="transfer"><button class="secondary export">JSON exportieren</button><label class="import">JSON oder CSV importieren<input type="file" accept=".json,.csv,application/json,text/csv"></label><p class="muted">CSV: week, weekday (1–7), meal, ingredients; Zutaten mit Semikolon trennen. Wochenzahl entspricht der Einstellung. Import ersetzt den gesamten Plan.</p></div></section><p class="foot">Wiederholung nach '+(this._data.weeks||12)+' Wochen · Start-Montag: '+this._esc(this._data.anchor_date||"—")+"</p></main>";
    this._bind();
  }
  // Attach handlers after each render because the panel replaces its shadow DOM.
  _bind() {
    this.shadowRoot.querySelector(".prev").onclick=()=>{this._weekStart.setDate(this._weekStart.getDate()-7);this._render();};
    this.shadowRoot.querySelector(".next").onclick=()=>{this._weekStart.setDate(this._weekStart.getDate()+7);this._render();};
    this.shadowRoot.querySelector(".current").onclick=()=>{this._weekStart=this._monday();this._render();};
    this.shadowRoot.querySelectorAll("select[data-slot]").forEach(el=>el.onchange=()=>this._run(async()=>{
      const slot=Number(el.dataset.slot); await this._api("set_day",{day_index:slot,meal_id:el.value||null}); this._data.schedule[slot]=el.value||null;
    },"Plan gespeichert."));
    this.shadowRoot.querySelectorAll("[data-shop]").forEach(el=>el.onclick=()=>this._run(()=>this._api("add_ingredients",{day_index:Number(el.dataset.shop)})));
    this.shadowRoot.querySelector(".add").onclick=()=>this._dialog();
    this.shadowRoot.querySelectorAll("[data-edit]").forEach(el=>el.onclick=()=>this._dialog(this._data.meals.find(m=>m.id===el.dataset.edit)));
    this.shadowRoot.querySelectorAll("[data-delete]").forEach(el=>el.onclick=async()=>{
      const meal=this._data.meals.find(m=>m.id===el.dataset.delete);
      if(meal&&confirm('"'+meal.name+'" löschen? Zugeordnete Plan-Tage werden geleert.')) await this._run(()=>this._api("delete_meal",{meal_id:meal.id}),"Gericht gelöscht.");
    });
    this.shadowRoot.querySelector(".export").onclick=()=>this._export();
    this.shadowRoot.querySelector("input[type=file]").onchange=ev=>this._import(ev);
  }
  async _run(action, success) {
    try {
      const result=await action();
      // Shopping-list actions return how many items were added or skipped.
      this._message=result&&typeof result.added==="number"?result.added+" Zutat(en) hinzugefügt; "+result.skipped+" bereits vorhanden oder doppelt.":(success||"Änderung gespeichert.");
      await this._load();
    } catch(err) { this._message="Aktion fehlgeschlagen: "+(err.message||err);this._render(); }
  }
  // The same dialog handles adding a meal and editing its name or ingredients.
  _dialog(meal=null) {
    const dlg=document.createElement("dialog");
    dlg.innerHTML="<form class='form'><h2>"+(meal?"Gericht ändern":"Gericht hinzufügen")+"</h2><label>Name<input name='name' required maxlength='120'></label><label>Zutaten, durch Komma getrennt<textarea name='ingredients' rows='3' placeholder='frische Tomaten, Passata, Basilikum'></textarea></label><div class='actions'><button type='button' class='secondary cancel'>Abbrechen</button><button class='primary'>Speichern</button></div></form>";
    this.shadowRoot.append(dlg);dlg.querySelector("[name=name]").value=meal?.name||"";dlg.querySelector("[name=ingredients]").value=(meal?.ingredients||[]).join(", ");
    dlg.querySelector(".cancel").onclick=()=>dlg.close();dlg.onclose=()=>dlg.remove();
    dlg.querySelector("form").onsubmit=ev=>{ev.preventDefault();const name=dlg.querySelector("[name=name]").value.trim();const ingredients=dlg.querySelector("[name=ingredients]").value.split(",").map(x=>x.trim()).filter(Boolean);dlg.close();this._run(()=>this._api("save_meal",{meal_id:meal?.id||null,name,ingredients}),"Gericht gespeichert.");};
    dlg.showModal();
  }
  // Export all meals and assignments for the currently configured cycle.
  _export() {
    const blob=new Blob([JSON.stringify(this._data,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download="rolling-mealplan.json";a.click();URL.revokeObjectURL(url);
  }
  async _import(ev) {
    const file=ev.target.files?.[0];if(!file)return;
    // Import replaces every meal and cycle slot, so ask before sending it to storage.
    if(!confirm("Der Import ersetzt die Gerichteliste und alle "+(this._data.weeks||12)+" Planwochen. Ein im JSON enthaltenes Start-Montag wird ebenfalls übernommen. Fortfahren?")){ev.target.value="";return;}
    try {
      let data;
      if(file.name.toLowerCase().endsWith(".csv"))data=this._csv(await file.text());
      else {data=JSON.parse(await file.text());if(Array.isArray(data.weeks)&&data.weeks.length===(this._data.weeks||12))data.schedule=data.weeks.flat();}
      await this._run(()=>this._api("import",{data}),"Import abgeschlossen.");
    } catch(err){this._message="Import fehlgeschlagen: "+(err.message||err);this._render();}
    finally{ev.target.value="";}
  }
  _csv(text) {
    // Respect quoted commas in CSV fields; semicolons separate ingredients inside their field.
    const parse=line=>{const out=[];let field="",q=false;for(let i=0;i<line.length;i++){const c=line[i];if(c==='"'&&q&&line[i+1]==='"'){field+='"';i++;}else if(c==='"')q=!q;else if(c===","&&!q){out.push(field.trim());field="";}else field+=c;}out.push(field.trim());return out;};
    const rows=text.replace(/^\uFEFF/,"").split(/\r?\n/).filter(x=>x.trim()).map(parse);
    if(rows.length<2)throw new Error("Die CSV-Datei enthält keine Planzeilen.");
    const head=rows.shift().map(x=>x.toLowerCase()),col=n=>head.indexOf(n);
    if(["week","weekday","meal","ingredients"].some(x=>col(x)<0))throw new Error("Erwartete Kopfzeile: week,weekday,meal,ingredients.");
    const weeks=this._data.weeks||12;
    const meals=[],ids=new Map(),schedule=Array(weeks*7).fill(null);
    for(const row of rows){const w=Number(row[col("week")]),d=Number(row[col("weekday")]),name=row[col("meal")]||"";
      if(!Number.isInteger(w)||w<1||w>weeks||!Number.isInteger(d)||d<1||d>7)throw new Error("week muss 1–"+weeks+" und weekday 1–7 sein.");
      if(!name.trim())continue;const key=name.trim().toLocaleLowerCase();let meal=ids.get(key);
      if(!meal){meal={id:"meal-"+Math.random().toString(36).slice(2),name:name.trim(),ingredients:(row[col("ingredients")]||"").split(";").map(x=>x.trim()).filter(Boolean)};ids.set(key,meal);meals.push(meal);}
      schedule[(w-1)*7+d-1]=meal.id;
    }
    return {version:1,anchor_date:this._data.anchor_date,meals,schedule};
  }
}
customElements.define("rolling-mealplan-panel",RollingMealplanPanel);
