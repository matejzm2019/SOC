const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const number = (value, digits = 2) => value == null ? '—' : new Intl.NumberFormat('sk-SK', {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(value);
const kw = watts => `${number(watts / 1000)} kW`;
const eur = value => value == null ? '—' : `${number(value)} €`;
const time = timestamp => new Date(timestamp).toLocaleTimeString('sk-SK', {hour:'2-digit', minute:'2-digit', timeZone:'Europe/Bratislava'});
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state, view = 'overview', period = 'day', settingsTab = 'source', busy = false, refreshing = false, revision = 0;
let lastDataAt = 0, lastDataKey = '', selectedRun = '', chatBusy = false, assistantStatus, historySettings;
let chatHistory = [], integrationsBusy = false, integrationCheckedAt = 0, weatherRequestedAt = 0, weatherRequestKey = '';
const pages = {
  overview: ['Prehľad', 'Prehľad domácnosti', 'Spotreba, výroba a tok energie na jednom mieste.'],
  history: ['História', 'Energia v čase', 'Priebeh spotreby a výroby.'],
  forecast: ['Predikcie', 'Predikcia na 24 hodín', 'Výhľad výroby a spotreby podľa dostupných údajov.'],
  economy: ['Ekonomika', 'Náklady na energiu', 'Odber, výkup a prevádzková úspora.']
};

async function api(path, options = {}) {
  const response = await fetch(`/api/${path}`, {cache:'no-store', ...options, headers:{'Content-Type':'application/json', ...options.headers}});
  if (!response.ok) {
    let message = `Chyba API (${response.status})`;
    try {
      const body = await response.json();
      message = Array.isArray(body.detail) ? body.detail.map(x => `${x.loc.at(-1)}: ${x.msg}`).join('; ') : body.detail || message;
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

function showError(error) {
  $('#error').textContent = `${error.message} Posledné zobrazené hodnoty môžu byť neaktuálne. Ďalší pokus prebehne automaticky.`;
  $('#error').hidden = false;
  $('#connection').textContent = 'Pripojenie prerušené';
}

function setText(id, value) { const el = $(`#${id}`); if (el.textContent !== String(value)) el.textContent = value; }
function metricValue(id, value, unit) { $(`#${id}`).innerHTML = `${number(value)}<small>${unit}</small>`; }
function acceptState(next, preserveChat = false) {
  if (!preserveChat && state && state.demo.run_id !== next.demo.run_id) {
    chatHistory = [];
    if (!chatBusy) {
      $('#chat-messages').replaceChildren();
      const empty = document.createElement('p'); empty.className = 'chat-empty';
      empty.textContent = 'Zdroj energetických údajov sa zmenil. Nové otázky použijú aktuálny prehľad.';
      $('#chat-messages').append(empty);
    }
  }
  state = next;
}

function updateModules() {
  $$('[data-module]').forEach(el => { const config = view === 'history' && el.closest('[data-page="history"]') && historySettings ? historySettings : state.settings; el.hidden = !config[`${el.dataset.module}_enabled`]; });
  // SVG elements do not consistently implement HTMLElement.hidden.
  $$('svg [data-module]').forEach(el => { el.style.display = state.settings[`${el.dataset.module}_enabled`] ? '' : 'none'; });
  if (view === 'economy' && !state.settings.prices_enabled) switchView('overview');
  $('#path-pv').style.display = state.settings.pv_enabled ? '' : 'none';
  $('#path-battery').style.display = state.settings.battery_enabled && state.demo.enabled ? '' : 'none';
}

function setFlow(id, value, reverse) {
  const path = $(`#path-${id}`);
  path.classList.toggle('reverse', reverse);
  path.classList.toggle('idle', Math.abs(value) < 1 || state.demo.paused || (!state.demo.enabled && !state.device.online));
}

function renderState() {
  const s = state.sample, settings = state.settings, demo = state.demo;
  updateModules();
  $$('[data-demo-control]').forEach(el => { el.hidden = !demo.enabled; });
  const imported = settings.measurement_source === 'csv', hybrid = !demo.enabled && settings.measurement_source === 'hybrid', waiting = hybrid && (s.seeded || s.source !== 'hybrid');
  const label = demo.enabled ? 'Demo režim' : imported ? 'Importovaná história' : 'Model domu · ESP32';
  setText('mode-title', label);
  setText('mode-pill', `◉ ${label}`);
  setText('energy-provenance', imported ? 'Spotreba a FV pochádzajú z importovaných intervalov. Tok siete je odvodený výpočtom; zobrazený výkon je priemer posledného intervalu.' : hybrid ? state.device.online ? 'ESP32 meria panel a nabitie malej Li-ion batérie. Toky domácnosti sú škálovaný model; ESP a svetlá napája laboratórny zdroj.' : 'ESP32 je odpojené. Čakám na meranie; posledné dostupné hodnoty môžu byť staré. Simulátor nenahrádza meranie.' : state.settings.weather_source === 'simulator' ? 'Energetické toky aj počasie pochádzajú zo simulátora.' : 'Energetické toky sú simulované. Internetové počasie je samostatný aktuálny údaj a nemení prezentačný scenár.');
  setText('flow-heading', imported ? 'Bilancia posledného intervalu' : 'Energetické toky');
  metricValue('load-value', s.load_w / 1000, 'kW');
  metricValue('pv-value', s.pv_w / 1000, 'kW');
  metricValue('soc-value', s.soc_pct, '%');
  metricValue('grid-value', Math.abs(s.grid_w) / 1000, 'kW');
  setText('load-detail', imported ? 'Priemer intervalu z CSV' : hybrid ? 'Model spotreby podľa záťaží ESP32' : `${number(s.voltage_v, 0)} V · ${number(s.current_a, 1)} A · virtuálne`);
  setText('pv-detail', `${number(settings.pv_kwp, 1)} kWp inštalovaný výkon`);
  if (s.source === 'hybrid') setText('pv-detail', `${number(s.panel_power_w, 3)} W panel · ${number(s.illuminance_lux, 0)} lx · ESP32`);
  if (imported) setText('pv-detail', 'Výroba z importovaného intervalu');
  if (waiting) ['load-value','pv-value','soc-value','grid-value'].forEach(id => setText(id, '—'));
  const batteryAction = s.battery_w > 1 ? 'Vybíjanie' : s.battery_w < -1 ? 'Nabíjanie' : 'Pohotovosť';
  setText('battery-detail', `${number(s.battery_energy_kwh, 1)} / ${number(settings.battery_kwh, 1)} kWh · ${batteryAction.toLowerCase()} · virtuálne`);
  setText('battery-title', hybrid ? 'Solárna Li-ion batéria' : 'Batéria domácnosti');
  if (hybrid) setText('battery-detail', s.battery_voltage_v == null ? 'MAX17048 · nabitie zatiaľ nie je dostupné' : `${number(s.battery_voltage_v,2)} V · ${number(settings.battery_capacity_mah,0)} mAh · MAX17048`);
  $('#physical-battery-panel').hidden = !hybrid || !settings.battery_enabled;
  const cellAvailable = hybrid && !waiting && s.battery_voltage_v != null;
  if (hybrid && !cellAvailable) { setText('soc-value', '—'); $('#soc-bar').style.width = '0%'; }
  const cellRate = s.battery_charge_rate_pct_h;
  setText('cell-soc', cellAvailable ? `${number(s.soc_pct,1)} %` : '—');
  setText('cell-voltage', cellAvailable ? `${number(s.battery_voltage_v,2)} V` : '—');
  setText('cell-capacity', `${number(settings.battery_capacity_mah,0)} mAh`);
  setText('cell-energy', cellAvailable ? `${number(s.battery_energy_kwh * 1000,2)} Wh` : '—');
  setText('cell-status', !state.device.online ? 'ESP32 OFFLINE' : cellAvailable ? 'MAX17048 · MERANIE' : 'ČAKÁM NA BATÉRIU');
  setText('cell-trend', !cellAvailable ? 'Pripojte kompatibilnú batériu a MAX17048. Bez merača sa nabitie neodhaduje z napätia.' : `${cellRate == null ? 'Trend zatiaľ nie je dostupný' : Math.abs(cellRate) < .5 ? 'SOC sa výrazne nemení' : cellRate > 0 ? 'SOC stúpa · pravdepodobné nabíjanie' : 'SOC klesá'}${cellRate == null ? '' : ` · zmena ${number(cellRate,1)} percentuálneho bodu/h (odhad)`} · ${time(s.timestamp)}${state.device.online ? '' : ' · posledné meranie'}`);
  $('#soc-bar').style.width = `${hybrid && !cellAvailable ? 0 : s.soc_pct || 0}%`;
  const gridAction = !s.grid_available ? 'Výpadok siete' : s.grid_w > 1 ? '↓ Odber zo siete' : s.grid_w < -1 ? '↑ Dodávka do siete' : 'Bez toku energie';
  setText('grid-detail', gridAction);
  setText('flow-load', kw(s.served_w));
  setText('flow-pv', kw(s.pv_w));
  setText('flow-pv-sub', `${number(settings.pv_kwp, 1)} kWp · virtuálna FV`);
  if (hybrid) setText('flow-pv-sub', 'Výkon škálovaný z merania panela');
  if (imported) setText('flow-pv-sub', 'Priemer importovaného intervalu');
  setText('energy-data-label', imported ? 'Importované intervaly' : hybrid ? 'Meranie panela + škálovaný model' : 'Syntetické dáta');
  setText('flow-grid', kw(Math.abs(s.grid_w)));
  setText('flow-grid-sub', gridAction);
  setText('flow-battery', `${s.battery_w > 1 ? '−' : s.battery_w < -1 ? '+' : ''}${kw(Math.abs(s.battery_w))}`);
  setText('flow-battery-label', hybrid ? '▱ SOLÁRNA BATÉRIA' : '▱ BATÉRIA');
  if (hybrid) setText('flow-battery', cellAvailable ? `${number(s.soc_pct,1)} %` : '—');
  $('#flow-battery').parentElement.setAttribute('aria-label', `${batteryAction}, ${s.battery_eta_hours == null ? 'odhad nedostupný' : number(s.battery_eta_hours, 1) + ' hodín do limitu'}`);
  setText('flow-wind', kw(s.wind_w));
  setText('mobile-pv', kw(s.pv_w));
  setText('mobile-load', kw(s.served_w));
  setText('mobile-battery', kw(Math.abs(s.battery_w)));
  $('#mobile-battery').previousElementSibling.textContent = hybrid ? '▱ Solárna Li-ion batéria' : '▱ Virtuálna batéria';
  if (hybrid) setText('mobile-battery', cellAvailable ? `${number(s.soc_pct,1)} %` : '—');
  setText('mobile-grid', kw(Math.abs(s.grid_w)));
  setText('mobile-grid-detail', gridAction);
  setFlow('pv', s.pv_w, false);
  setFlow('grid', s.grid_w, s.grid_w < 0);
  setFlow('battery', s.battery_w, s.battery_w > 0);
  setFlow('wind', s.wind_w, false);
  setText('flow-status', imported || hybrid ? '● VYPOČÍTANÁ BILANCIA' : s.grid_available ? '● SIEŤ DOSTUPNÁ' : '○ OSTROVNÝ REŽIM');
  setText('balance-caption', s.unserved_w > 1 ? `Nepokrytá spotreba ${kw(s.unserved_w)}` : 'Celá spotreba pokrytá');
  const eta = s.battery_eta_hours == null ? '' : ` · do limitu ${number(s.battery_eta_hours, 1)} h`;
  setText('unserved', s.curtailed_w > 1 ? `Obmedzená výroba ${kw(s.curtailed_w)}` : `${settings.battery_enabled ? batteryAction + eta : 'Batéria vypnutá'}`);
  if (hybrid) {
    setText('unserved', 'Batéria má samostatný solárny okruh');
    $('#flow-battery').parentElement.setAttribute('aria-label', 'Malá solárna batéria; ESP a svetlá napája laboratórny zdroj');
  }
  if (waiting) {
    ['flow-load','flow-pv','flow-grid','flow-battery','flow-wind','mobile-load','mobile-pv','mobile-grid','mobile-battery'].forEach(id => setText(id,'—'));
    ['grid-detail','flow-grid-sub','mobile-grid-detail','balance-caption','unserved','battery-detail'].forEach(id => setText(id,'Čakám na meranie ESP32'));
    setText('flow-status','○ ČAKÁM NA ÚDAJE');
    $('#soc-bar').style.width = '0%';
    $('#flow-battery').parentElement.setAttribute('aria-label','Čakám na meranie ESP32');
  }
  renderWeather(state.weather);
  const internetPrice = settings.price_source === 'internet', prices = state.prices || {};
  setText('buy-price', internetPrice ? prices.available ? `${number(prices.buy_eur_kwh,4)} €` : '—' : eur(s.buy_eur_kwh));
  setText('sell-price', eur(settings.sell_price));
  setText('tariff-source', internetPrice ? prices.stale ? 'SPOT SK · CACHE' : 'SPOT SK · INTERNET' : demo.enabled ? 'DEMO TARIFA' : 'VLASTNÁ TARIFA');
  setText('tariff-note', `${internetPrice ? `Spot + prirážka, DPH ${number(settings.energy_vat_pct,0)} %. ${prices.fetched_at ? `Získané ${time(prices.fetched_at)}. ` : ''}${prices.error || 'Trhová cena sa môže líšiť od faktúry.'} ` : ''}Distribúcia ${eur(settings.distribution_price)}/kWh · fix ${eur(settings.fixed_daily)}/deň. Výkup zo zmluvy.`);
  $('#scenario').value = demo.scenario;
  $('#speed').value = demo.speed;
  setText('play', demo.paused ? '▶ Spustiť' : 'Ⅱ Pozastaviť');
  $('#play').hidden = imported;
  const date = new Date(s.timestamp).toLocaleDateString('sk-SK', {day:'numeric', month:'short', timeZone:'Europe/Bratislava'});
  setText('sim-clock', imported ? `${date} ${time(s.timestamp)} · posledný importovaný interval` : hybrid ? waiting ? 'Čakám na prvé meranie ESP32' : `${date} ${time(s.timestamp)} · ${!state.device.online ? 'posledné meranie · ESP32 offline' : demo.paused ? 'pozastavené' : 'aktualizácia každú sekundu'}` : demo.enabled
    ? `${date} ${time(s.timestamp)} · ${demo.paused ? 'pozastavené' : `1 s ≈ ${demo.speed * 5} min`} · demo čas`
    : `${date} ${time(s.timestamp)} · ${demo.paused ? 'pozastavené' : 'vzorka každú 1 s'} · reálny čas`);
  setText('run-info', `${label} #${demo.run_id} · Europe/Bratislava`);
  setText('device-status', hybrid ? (state.device.online ? '● ESP32 ONLINE' : '○ ESP32 OFFLINE') : imported ? 'CSV INTERVALY' : 'SIMULÁTOR');
  $('#device-status').classList.toggle('device-offline', hybrid && !state.device.online);
  $('#insights').innerHTML = waiting ? '<p class="muted">Odporúčania budú dostupné po prvom meraní ESP32.</p>' : state.summary.items.map(item => `<article class="insight ${escape(item.kind)}"><h3>${escape(item.title)}</h3><p>${escape(item.text)}</p></article>`).join('');
  if (demo.error) { $('#error').textContent = demo.error; $('#error').hidden = false; }
}

function series(settings = state.settings) {
  const color = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return [{key:'load_w', color:color('--load'), name:'Spotreba'},
    ...(settings.pv_enabled ? [{key:'pv_w', color:color('--solar'), name:'Fotovoltaika'}] : []),
    ...(settings.wind_enabled ? [{key:'wind_w', color:color('--wind'), name:'Vietor'}] : [])];
}

function chart(id, points, lines = series(), unit = 'kW') {
  const container = $(`#${id}`);
  if (!points.length) { container.textContent = 'Zatiaľ nie sú dostupné dáta.'; return; }
  const width = Math.max(300, container.clientWidth || 800);
  const height = container.classList.contains('tall') ? 300 : 200;
  const left = 42, right = 15, top = 16, bottom = 32;
  const scale = unit === '%' ? 1 : 1000;
  const values = points.flatMap(p => lines.filter(l => p[l.key] != null).map(l => p[l.key] / scale));
  if (!values.length) { container.textContent = 'Meranie zatiaľ nie je dostupné.'; return; }
  const maximum = unit === '%' ? 100 : Math.max(1, Math.ceil(Math.max(...values) * 1.12));
  const minimum = Math.min(0, Math.floor(Math.min(...values)));
  const x = i => left + i / Math.max(1, points.length - 1) * (width - left - right);
  const y = n => top + (maximum - n) / (maximum - minimum) * (height - top - bottom);
  let content = `<title>${escape(id === 'soc-chart' ? 'História SOC batérie' : 'Časový graf spotreby a výroby')}</title>`;
  for (let i = 0; i <= 4; i++) {
    const value = minimum + (maximum - minimum) * i / 4;
    content += `<line class="grid-line" x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}"/><text x="${left - 10}" y="${y(value) + 4}" text-anchor="end">${number(value, unit === '%' ? 0 : 1)}</text>`;
  }
  content += `<text x="5" y="9">${unit}</text>`;
  lines.forEach(line => {
    const coords = points.map((p, i) => p[line.key] == null ? null : `${x(i)},${y(p[line.key] / scale)}`);
    if (line.key === 'load_w' && coords.every(Boolean)) content += `<path d="M${x(0)},${y(0)} L${coords.join(' L')} L${x(points.length - 1)},${y(0)} Z" fill="${line.color}" opacity=".035"/>`;
    let path = '', connected = false;
    coords.forEach(coord => { if (coord) { path += `${connected ? ' L' : ' M'}${coord}`; connected = true; } else connected = false; });
    content += `<path class="plot-line" stroke="${line.color}" d="${path}"/>`;
    if (coords.filter(Boolean).length === 1) { const [cx,cy] = coords.find(Boolean).split(','); content += `<circle cx="${cx}" cy="${cy}" r="3" fill="${line.color}"/>`; }
  });
  const ticks = width < 420 ? 4 : 6;
  for (let i = 0; i < ticks; i++) {
    const index = Math.round((points.length - 1) * i / (ticks - 1));
    content += `<text x="${x(index)}" y="${height - 7}" text-anchor="${i === 0 ? 'start' : i === ticks - 1 ? 'end' : 'middle'}">${time(points[index].timestamp)}</text>`;
  }
  points.forEach((point, i) => {
    const tooltip = `${new Date(point.timestamp).toLocaleString('sk-SK', {timeZone:'Europe/Bratislava'})}\n${lines.map(l => `${l.name}: ${number(point[l.key] == null ? null : point[l.key] / scale)} ${unit}`).join('\n')}`;
    content += `<rect aria-hidden="true" x="${x(i) - (width - left - right) / points.length / 2}" y="${top}" width="${Math.max(2,(width - left - right) / points.length)}" height="${height - top - bottom}" fill="transparent"><title>${escape(tooltip)}</title></rect>`;
  });
  container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escape(lines.map(l => l.name).join(', '))} v ${unit}">${content}</svg>`;
}

function spark(id, points, field) {
  const values = points.slice(-36).map(p => Math.abs(p[field] ?? 0)), max = Math.max(1, ...values);
  $(`#spark-${id}`).innerHTML = `<polyline points="${values.map((v,i) => `${i / Math.max(1,values.length - 1) * 180},${32 - v / max * 26}`).join(' ')}"/>`;
}

function cards(container, entries) {
  $(`#${container}`).innerHTML = entries.map(([label,value,unit,caption]) => `<article class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value == null ? '—' : number(value)}<small>${unit}</small></div><div class="metric-foot">${caption}</div></article>`).join('');
}

function renderHistory(history) {
  const t = history.totals;
  if (view === 'overview') {
    chart('overview-chart', history.points);
    spark('load', history.points, 'load_w'); spark('pv', history.points, 'pv_w'); spark('grid', history.points, 'grid_w');
    setText('today-energy', `24 h: spotreba ${number(t.load_kwh)} kWh${state.settings.pv_enabled ? ` · FV ${number(t.pv_kwh)} kWh` : ''}`);
  }
  if (view === 'history') {
    const config = history.config || state.settings;
    historySettings = config;
    $$('[data-page="history"] [data-module]').forEach(el => el.hidden = !config[`${el.dataset.module}_enabled`]);
    chart('history-chart', history.points, series(config));
    chart('soc-chart', history.points, [{key:'soc_pct', color:getComputedStyle(document.documentElement).getPropertyValue('--battery').trim(), name:'SOC'}], '%');
    const entries = [['Spotreba',t.load_kwh,'kWh','Požadovaný odber'], ['Import zo siete',t.import_kwh,'kWh','Nakúpená energia'], ['Export do siete',t.export_kwh,'kWh','Dodaná energia'], ['Nepokrytá spotreba',t.unserved_kwh,'kWh','Počas výpadku']];
    if (config.pv_enabled) entries.push(['Výroba FV',t.pv_kwh,'kWh',config.measurement_source === 'csv' ? 'Importované intervaly' : 'Modelovaná elektráreň']);
    if (config.wind_enabled) entries.push(['Výroba vetra',t.wind_kwh,'kWh','Virtuálna turbína']);
    cards('history-totals', entries);
    setText('history-coverage', `${history.sample_count} vzoriek · ${number(history.duration_hours, 1)} h · ${history.seeded_count} predgenerovaných`);
  }
  if (view === 'economy') {
    cards('economy-totals', [['Čisté náklady',t.cost_eur,'€','Po odpočítaní výkupu'], ['Prevádzková úspora',t.savings_eur,'€','Voči nákupu zo siete'], ['Príjem z exportu',t.export_revenue_eur,'€','Výkup prebytkov'], ['Referenčné náklady',t.reference_eur,'€','Bez lokálnej výroby']]);
    $('#economy-breakdown').innerHTML = [['Odber zo siete',`${number(t.import_kwh)} kWh`],['Dodávka do siete',`${number(t.export_kwh)} kWh`],['Obslúžená spotreba',`${number(t.served_kwh)} kWh`],['Dĺžka výpočtového obdobia',`${number(history.duration_hours,1)} h`],['Náklady vrátane poplatkov',eur(t.cost_eur)],['Rozdiel voči referencii',eur(t.savings_eur)]].map(([a,b]) => `<div><span>${a}</span><strong>${b}</strong></div>`).join('');
    $('#economy-breakdown').insertAdjacentHTML('beforeend', `<p class="footnote">${t.cost_eur == null ? 'Náklady nie sú dostupné: niektorým intervalom chýba cena alebo je modul vypnutý. Chýbajúce ceny nenahrádzame nulou.' : 'Výpočet používa ceny uložené pri každom intervale. Škálovaná spotreba modelu nie je faktúra za laboratórny zdroj.'}</p>`);
  }
}

function renderForecast(result) {
  setText('forecast-note', result.note || result.reason || 'Čakám na dostupné údaje.');
  setText('forecast-method', result.weather_based ? 'POČASIE + MODEL' : 'ČASOVÝ MODEL');
  setText('forecast-model', result.available ? result.model : result.reason);
  chart('forecast-chart', result.points || []);
  const labels = {load_w:'Spotreba', pv_w:'Fotovoltaika', wind_w:'Vietor'};
  setText('forecast-metrics', result.metrics ? Object.entries(result.metrics).filter(([key]) => key === 'load_w' || state.settings[key === 'pv_w' ? 'pv_enabled' : 'wind_enabled']).map(([key,m]) => `${labels[key]}: MAE ${number(m.mae_w,0)} W · RMSE ${number(m.rmse_w,0)} W`).join(' | ') : 'Hodnotenie časového modelu potrebuje súvislých 48 hodín intervalovej histórie. Meteorologická predikcia FV sa tu nepovažuje za overenú meraním.');
}

async function refresh(forceData = false) {
  if (refreshing || busy) return;
  refreshing = true;
  const requestedView = view;
  const requestedRevision = revision;
  try {
    const nextState = await api('state');
    if (requestedRevision !== revision) return;
    const firstLoad = !state;
    acceptState(nextState);
    if (firstLoad && view === 'history') loadRuns();
    $('#error').hidden = true;
    $('#connection').innerHTML = '<i class="online-dot"></i>Lokálne pripojenie';
    renderState();
    const dataKey = `${view}:${period}:${state.demo.run_id}:${selectedRun}`;
    const interval = view === 'forecast' ? 10000 : 1500;
    if (forceData || dataKey !== lastDataKey || Date.now() - lastDataAt >= interval) {
      const data = await api(view === 'forecast' ? 'forecast' : `history?period=${view === 'history' ? period : 'day'}${view === 'history' && selectedRun ? `&run_id=${selectedRun}` : ''}`);
      if (requestedRevision !== revision) return;
      lastDataAt = Date.now(); lastDataKey = dataKey;
      if (requestedView === view) {
        if (view === 'forecast') renderForecast(data); else renderHistory(data);
      }
    }
    if (!state.settings.configured && !$('#setup').open) openSetup();
  } catch (error) { showError(error); }
  finally { refreshing = false; }
}

async function command(payload) {
  if (busy) return;
  revision++;
  busy = true;
  $$('.demo-toolbar button, .demo-toolbar select').forEach(el => el.disabled = true);
  try { acceptState(await api('demo', {method:'POST', body:JSON.stringify(payload)})); renderState(); }
  catch (error) { showError(error); }
  finally { busy = false; $$('.demo-toolbar button, .demo-toolbar select').forEach(el => el.disabled = false); }
  await refresh(true);
}

function switchView(name) {
  if (!pages[name]) name = 'overview';
  view = name;
  revision++;
  $$('[data-page]').forEach(el => el.hidden = el.dataset.page !== name);
  $$('[data-view]').forEach(el => { el.classList.toggle('active', el.dataset.view === name); el.setAttribute('aria-current', el.dataset.view === name ? 'page' : 'false'); });
  const [crumb,title,description] = pages[name];
  setText('breadcrumb', crumb); setText('page-title', title); setText('page-description', description);
  history.replaceState(null, '', `#${name}`);
  if (name === 'history') loadRuns();
  updateExportLink();
  refresh(true);
}

const form = $('#setup-form');
form.noValidate = true;
function selectSettingsTab(name) {
  settingsTab = name;
  $$('[data-settings-tab]').forEach(el => { el.classList.toggle('active', el.dataset.settingsTab === name); el.setAttribute('aria-current', el.dataset.settingsTab === name ? 'page' : 'false'); });
  $$('[data-settings-panel]').forEach(el => el.hidden = el.dataset.settingsPanel !== name);
}
function formSettings() {
  const values = {...state.settings, configured:true};
  for (const field of form.elements) {
    if (!field.name || field.disabled) continue;
    values[field.name] = field.type === 'checkbox' ? field.checked : field.type === 'number' ? Number(field.value) : field.value;
  }
  return values;
}
function updateSettings() {
  const source = form.elements.namedItem('measurement_source').value;
  const imported = source === 'csv';
  const weatherSource = form.elements.namedItem('weather_source');
  weatherSource.querySelector('[value="simulator"]').disabled = source === 'hybrid';
  if (source === 'hybrid') weatherSource.value = 'internet';
  ['battery_enabled','wind_enabled'].forEach(name => { form.elements.namedItem(name).disabled = imported; if (imported) form.elements.namedItem(name).checked = false; });
  $$('[data-setting-module]').forEach(el => {
    el.hidden = !form.elements.namedItem(`${el.dataset.settingModule}_enabled`).checked;
    el.querySelector('input').disabled = el.hidden;
  });
  $$('[data-battery-model]').forEach(el => {
    el.hidden = !form.elements.namedItem('battery_enabled').checked || (el.dataset.batteryModel === 'physical' ? source !== 'hybrid' : source !== 'simulator');
    el.querySelector('input').disabled = el.hidden;
  });
  const calibration = form.elements.namedItem('pv_reference_w');
  calibration.closest('label').hidden = source !== 'hybrid' || !form.elements.namedItem('pv_enabled').checked;
  calibration.disabled = calibration.closest('label').hidden;
  const prices = form.elements.namedItem('prices_enabled').checked;
  $('#price-settings').hidden = !prices;
  $('#prices-disabled').hidden = prices;
  $$('#price-settings input, #price-settings select').forEach(el => el.disabled = !prices);
  const internet = form.elements.namedItem('price_source').value === 'internet';
  $$('[data-price-source]').forEach(el => { el.hidden = !prices || (el.dataset.priceSource === 'internet') !== internet; el.querySelector('input,select').disabled = el.hidden; });
  const offpeak = prices && !internet && form.elements.namedItem('price_mode').value === 'time_of_use';
  $('#offpeak-field').hidden = !offpeak;
  form.elements.namedItem('offpeak_price').disabled = !offpeak;
  setText('price-explainer', internet ? 'Energy-Charts: aktuálny slovenský spot v €/kWh, obnovenie každých 30 minút. Nákup = (spot + prirážka) × (1 + DPH). Výkup zadajte podľa zmluvy; distribúciu a fixné poplatky vrátane príslušných daní. SK dáta sú na súkromné použitie; na verejné demo použite ručnú tarifu. Pri výpadku používame iba platný uložený interval.' : 'Zadajte cenu zo zmluvy vrátane daní. V demo režime scenáre lacnej a drahej energie dočasne upravia ručnú nákupnú cenu.');
  const hybrid = source === 'hybrid';
  setText('source-explainer', hybrid ? 'ESP32-S3 posiela meranie panela a MAX17048 cez Wi-Fi. Batériu nabíja solárna nabíjačka; ostatné zariadenia napája laboratórny zdroj. Toky domácnosti sú modelované.' : imported ? 'Importujte vlastné údaje tlačidlom nižšie. Import sa spracuje samostatne a zachová doterajšiu históriu.' : 'Simulátor vytvára syntetické energetické údaje a pripravené scenáre. Funguje aj bez internetu.');
  setText('settings-device-state', hybrid ? (state.device.online ? 'ESP32 pripojené' : 'ESP32 nepripojené') : imported ? 'Vlastná história' : 'Lokálny simulátor');
  setText('chosen-location', form.elements.namedItem('location_set').checked ? `${form.elements.namedItem('location_name').value} · ${number(Number(form.elements.namedItem('latitude').value),3)}°, ${number(Number(form.elements.namedItem('longitude').value),3)}°` : 'Miesto nie je nastavené');
  setText('ollama-command', `ollama pull ${form.elements.namedItem('ai_model').value}`);
  const values = formSettings();
  const changed = Object.keys(state.settings).filter(key => values[key] !== state.settings[key]);
  const count = changed.length;
  const reset = changed.some(key => !['ai_enabled','ai_model','weather_enabled','location_name','location_set','weather_source'].includes(key));
  setText('settings-change-title', count ? `${count} ${count === 1 ? 'zmena' : count < 5 ? 'zmeny' : 'zmien'} na uloženie` : 'Žiadne neuložené zmeny');
  setText('settings-change-detail', count ? reset ? imported ? 'Uloženie vytvorí novú analýzu importovaných údajov s touto tarifou. Pôvodná história zostane uložená.' : 'Zmena modelu vytvorí nový súbor údajov. Normálny režim čaká na ESP32; demo začína pozastavené.' : 'Nastavenia sa uložia bez resetovania energetickej histórie.' : 'Upravte hodnotu alebo modul. Vzhľad stránky sa prepína okamžite mimo nastavení.');
  $('#settings-save').disabled = !count || busy;
}
function openSetup() {
  if (!state) return;
  for (const [key,value] of Object.entries(state.settings)) {
    const field = form.elements.namedItem(key);
    if (field) { if (field.type === 'checkbox') field.checked = value; else field.value = value; }
  }
  selectSettingsTab('source'); setText('setup-error', ''); updateSettings();
  $('#setup-close').hidden = !state.settings.configured;
  $('#settings-cancel').hidden = !state.settings.configured;
  $('#setup').showModal();
}
$$('[data-settings-tab]').forEach(el => el.addEventListener('click', () => selectSettingsTab(el.dataset.settingsTab)));
$('#setup-close').addEventListener('click', () => $('#setup').close());
$('#settings-cancel').addEventListener('click', () => $('#setup').close());
$('#setup').addEventListener('cancel', event => { if (!state.settings.configured) event.preventDefault(); });
form.addEventListener('input', updateSettings);
form.addEventListener('change', event => {
  const source = form.elements.namedItem('measurement_source'), demo = form.elements.namedItem('demo_mode');
  if (event.target.name === 'demo_mode') source.value = demo.checked ? 'simulator' : 'hybrid';
  if (event.target.name === 'measurement_source') demo.checked = source.value === 'simulator';
  updateSettings();
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  const invalid = $$('[data-settings-panel] input, [data-settings-panel] select').find(field => !field.disabled && !field.checkValidity());
  if (invalid) {
    selectSettingsTab(invalid.closest('[data-settings-panel]').dataset.settingsPanel);
    invalid.reportValidity();
    return;
  }
  const settings = formSettings();
  if (Object.keys(settings).every(key => settings[key] === state.settings[key])) return;
  revision++; busy = true; $('#settings-save').disabled = true;
  try {
    acceptState(await api('settings', {method:'PUT', body:JSON.stringify(settings)}));
    $('#setup').close(); renderState();
    weatherRequestKey = ''; integrationCheckedAt = 0; refreshIntegrations(); loadRuns();
  } catch (error) { setText('setup-error', error.message); }
  finally { busy = false; updateSettings(); }
  refresh(true);
});

function renderWeather(weather = {}) {
  const synthetic = state.settings.weather_source === 'simulator';
  const current = synthetic ? state.sample : weather.available ? weather.current : null;
  setText('weather-source', synthetic ? 'SIMULÁTOR' : weather.stale ? 'STARŠIE ÚDAJE' : weather.available ? 'OPEN-METEO' : 'ČAKÁM NA ÚDAJE');
  setText('temperature', current ? `${number(current.temperature_c,0)}°C` : '—');
  const description = current?.condition || (current ? current.cloud_pct > 65 ? 'Zamračené' : current.radiation_wm2 > 20 ? 'Prevažne slnečno' : 'Nízke slnečné žiarenie' : state.settings.location_set ? 'Počasie zatiaľ nie je dostupné' : 'Vyberte miesto v nastaveniach');
  setText('weather-condition', description);
  setText('weather-icon', description === 'Jasno' || description === 'Prevažne slnečno' ? '☀' : description.includes('Dážď') ? '☂' : '☁');
  for (const [id,key,unit,digits] of [['wind-weather','wind_ms','m/s',1],['cloud-weather','cloud_pct','%',0],['radiation-weather','radiation_wm2','W/m²',0]]) setText(id, current ? `${number(current[key],digits)} ${unit}` : '—');
  setText('location', synthetic ? 'Virtuálne počasie scenára' : state.settings.location_name || 'Miesto nie je nastavené');
  setText('weather-update', !synthetic && weather.available ? `Platnosť ${time(current.timestamp)} · získané ${time(weather.fetched_at)}` : '');
  setText('weather-error', synthetic ? '' : weather.stale ? 'Údaje sú staršie ako pol hodiny. Aktuálne počasie sa nepodarilo obnoviť.' : weather.error || '');
  $('.weather-attribution').hidden = synthetic;
  const now = Date.now();
  const hours = !synthetic && weather.available ? weather.hourly.filter(p => new Date(p.timestamp).getTime() > now).slice(0,6) : [];
  $('#weather-forecast').innerHTML = hours.map(p => `<div><span>${time(p.timestamp)}</span><strong>${number(p.temperature_c,0)}°</strong><small>${number(p.precipitation_mm,1)} mm</small></div>`).join('');
}

function updateExportLink() {
  $('#export-link').href = `/api/export${view === 'history' && selectedRun ? `?run_id=${selectedRun}` : ''}`;
}

async function loadRuns() {
  if (!state) return;
  try {
    const {runs} = await api('runs');
    const select = $('#history-run');
    select.innerHTML = '<option value="">Aktuálny súbor údajov</option>' + runs.filter(run => run.id !== state.demo.run_id).map(run => `<option value="${run.id}">#${run.id} · ${run.config.measurement_source === 'csv' ? 'CSV' : run.config.demo_mode ? 'demo' : 'model'} · ${run.end ? escape(new Date(run.end).toLocaleDateString('sk-SK')) : 'bez záznamov'} · ${run.count} vzoriek</option>`).join('');
    if (selectedRun && !runs.some(run => String(run.id) === selectedRun)) selectedRun = '';
    select.value = selectedRun;
  } catch (error) { setText('history-coverage', error.message); }
}

function applyAssistantStatus(result) {
  assistantStatus = result;
  setText('assistant-status', result.available ? result.model.toUpperCase() : 'NEPRIPOJENÝ');
  setText('assistant-connection', result.message);
  $$('.assistant-prompts button, #chat-send').forEach(el => el.disabled = chatBusy || !result.available);
  setText('chat-send', chatBusy ? 'Spracúva…' : 'Odoslať ↑');
  $('.assistant-panel').setAttribute('aria-busy', String(chatBusy));
}

async function refreshIntegrations() {
  if (!state || integrationsBusy) return;
  integrationsBusy = true;
  try {
    const key = `${state.settings.latitude}:${state.settings.longitude}:${state.settings.weather_source}:${state.settings.tilt_deg}:${state.settings.azimuth_deg}:${state.settings.location_set}`;
    const tasks = [];
    if (state.settings.location_set && state.settings.weather_source === 'internet' && (key !== weatherRequestKey || Date.now() - weatherRequestedAt > 600000)) {
      weatherRequestKey = key; weatherRequestedAt = Date.now();
      tasks.push(api('weather').then(result => {
        if (state && key === `${state.settings.latitude}:${state.settings.longitude}:${state.settings.weather_source}:${state.settings.tilt_deg}:${state.settings.azimuth_deg}:${state.settings.location_set}`) { state.weather = result; renderWeather(result); lastDataAt = 0; }
      }).catch(error => setText('weather-error', error.message)));
    }
    if (Date.now() - integrationCheckedAt > 30000) {
      integrationCheckedAt = Date.now();
      tasks.push(api('assistant/status').then(applyAssistantStatus).catch(error => applyAssistantStatus({available:false,message:error.message})));
    }
    await Promise.allSettled(tasks);
  } finally { integrationsBusy = false; }
}

function setLocation(latitude, longitude, label) {
  form.elements.namedItem('latitude').value = Number(latitude).toFixed(3);
  form.elements.namedItem('longitude').value = Number(longitude).toFixed(3);
  form.elements.namedItem('location_name').value = label.slice(0,120);
  form.elements.namedItem('location_set').checked = true;
  $('#location-results').replaceChildren();
  setText('location-error', ''); updateSettings();
}

$('#city-search').addEventListener('click', async () => {
  const query = $('#city-query').value.trim();
  if (query.length < 2) { setText('location-error', 'Zadajte aspoň dva znaky názvu mesta.'); return; }
  $('#city-search').disabled = true; setText('location-error', '');
  try {
    const result = await api(`locations?q=${encodeURIComponent(query)}`);
    $('#location-results').replaceChildren();
    if (!result.locations.length) setText('location-error', 'Mesto sa nenašlo. Skúste dlhší alebo iný názov.');
    result.locations.forEach(location => {
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = [location.name,location.region,location.country].filter(Boolean).join(' · ');
      button.addEventListener('click', () => setLocation(location.latitude,location.longitude,[location.name,location.country].filter(Boolean).join(', ')));
      $('#location-results').append(button);
    });
  } catch (error) { setText('location-error', error.message); }
  finally { $('#city-search').disabled = false; }
});
$('#city-query').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); $('#city-search').click(); } });
$('#gps-location').addEventListener('click', () => {
  if (!window.isSecureContext || !navigator.geolocation) { setText('location-error', 'Prehliadač povoľuje polohu iba cez HTTPS alebo localhost. Zadajte mesto.'); return; }
  $('#gps-location').disabled = true; setText('location-error', 'Čakám na povolenie polohy…');
  navigator.geolocation.getCurrentPosition(position => {
    setLocation(position.coords.latitude,position.coords.longitude,'Moja oblasť (GPS)'); $('#gps-location').disabled = false;
  }, error => {
    setText('location-error', error.code === 1 ? 'Prístup k polohe ste nepovolili. Môžete zadať mesto.' : 'Polohu sa nepodarilo určiť. Zadajte mesto.');
    $('#gps-location').disabled = false;
  }, {enableHighAccuracy:false,timeout:12000,maximumAge:300000});
});
$('#weather-location-button').addEventListener('click', () => { openSetup(); selectSettingsTab('location'); });

$('#assistant-check').addEventListener('click', async () => {
  $('#assistant-check').disabled = true;
  try { const result = await api(`assistant/status?model=${encodeURIComponent(form.elements.namedItem('ai_model').value)}`); setText('assistant-check-result', result.message); }
  catch (error) { setText('assistant-check-result', error.message); }
  finally { $('#assistant-check').disabled = false; }
});

$('#csv-file').addEventListener('change', event => {
  const file = event.target.files[0];
  $('#csv-import').disabled = !file || file.size > 3000000;
  setText('csv-file-info', file ? `${file.name} · ${number(file.size / 1024,0)} kB` : 'Žiadny súbor');
  setText('csv-error', file?.size > 3000000 ? 'Maximálna veľkosť CSV je 3 MB.' : '');
});
$('#csv-import').addEventListener('click', async () => {
  const file = $('#csv-file').files[0];
  if (!file || busy || file.size > 3000000) return;
  busy = true; revision++; $('#csv-import').disabled = true;
  try {
    acceptState(await api('import', {method:'POST',body:JSON.stringify({content:await file.text()})}));
    $('#setup').close(); chatHistory = []; renderState(); loadRuns();
  } catch (error) { setText('csv-error', error.message); }
  finally { busy = false; $('#csv-import').disabled = false; }
  refresh(true);
});

function chatBubble(role, text) {
  $('.chat-empty')?.remove();
  const article = document.createElement('article'); article.className = `chat-bubble ${role}`;
  const caption = document.createElement('small'); caption.textContent = role === 'user' ? 'Vy' : 'Lokálny asistent';
  const paragraph = document.createElement('p'); paragraph.textContent = text;
  article.append(caption,paragraph); $('#chat-messages').append(article);
  $('#chat-messages').scrollTop = $('#chat-messages').scrollHeight;
  return article;
}

function chatProposal(article, proposal) {
  const panel = document.createElement('section'); panel.className = 'chat-proposal';
  const title = document.createElement('h3'); title.textContent = 'Navrhnutá zmena';
  const values = document.createElement('dl'); values.className = 'assistant-facts';
  const labels = {internet:'Internet',manual:'Ručne',simulator:'Simulátor',time_of_use:'Časová tarifa'};
  const valueText = value => typeof value === 'boolean' ? value ? 'Zapnuté' : 'Vypnuté' : typeof value === 'number' ? number(value,4).replace(/0+$/,'').replace(/,$/,'') : labels[value] || value;
  proposal.changes.forEach(change => {
    const name = document.createElement('dt'), value = document.createElement('dd');
    name.textContent = change.label; value.textContent = `${valueText(change.before)} → ${valueText(change.after)}`;
    values.append(name,value);
  });
  const note = document.createElement('p'); note.className = 'footnote';
  note.textContent = 'Zmena parametrov môže začať nový súbor údajov. Predchádzajúca história zostane uložená. Chat nemení fyzické napájanie ani nabíjačku.';
  const actions = document.createElement('div'); actions.className = 'chat-proposal-actions';
  const apply = document.createElement('button'), cancel = document.createElement('button');
  apply.type = cancel.type = 'button'; apply.className = 'button primary'; cancel.className = 'button secondary';
  apply.textContent = 'Použiť zmenu'; cancel.textContent = 'Zrušiť návrh';
  const feedback = document.createElement('p'); feedback.className = 'form-error'; feedback.setAttribute('role','status');
  cancel.addEventListener('click', () => { panel.replaceChildren(); panel.textContent = 'Návrh zrušený. Nastavenia sa nezmenili.'; chatHistory.push({role:'assistant',content:panel.textContent}); chatHistory = chatHistory.slice(-6); });
  apply.addEventListener('click', async () => {
    if (busy || chatBusy) { feedback.textContent = 'Počkajte na dokončenie aktuálnej operácie.'; return; }
    busy = true; revision++; apply.disabled = cancel.disabled = true; apply.textContent = 'Ukladám…'; feedback.textContent = '';
    try {
      acceptState(await api('assistant/apply',{method:'POST',body:JSON.stringify({token:proposal.token})}),true);
      renderState(); actions.remove(); feedback.textContent = 'Zmena uložená.';
      const message = `Uložil som: ${proposal.changes.map(change => `${change.label}: ${valueText(change.after)}`).join('; ')}. Prehľad používa nové nastavenia; môžeš sa pýtať ďalej.`;
      chatBubble('assistant',message); chatHistory.push({role:'assistant',content:message.slice(0,1800)}); chatHistory = chatHistory.slice(-6);
      weatherRequestKey = ''; integrationCheckedAt = 0; refreshIntegrations(); loadRuns();
    } catch (error) { feedback.textContent = error.message; apply.disabled = cancel.disabled = false; apply.textContent = 'Použiť zmenu'; }
    finally { busy = false; refresh(true); }
  });
  actions.append(apply,cancel); panel.append(title,values,note,actions,feedback); article.append(panel);
}

async function askAssistant(question) {
  if (chatBusy || !question.trim()) return;
  chatBusy = true; setText('chat-error',''); applyAssistantStatus(assistantStatus || {available:false,message:'Pripájam model…'});
  chatBubble('user',question);
  const pending = chatBubble('assistant','Lokálny model spracúva otázku. Na staršom počítači to môže chvíľu trvať.');
  pending.classList.add('pending');
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(),125000);
  try {
    const result = await api('assistant/chat',{method:'POST',body:JSON.stringify({question,history:chatHistory.slice(-4)}),signal:controller.signal});
    pending.remove();
    const article = chatBubble('assistant',result.answer);
    applyAssistantStatus({available:true,model:result.model,message:'Pripravený na tomto počítači.'});
    article.querySelector('small').textContent = `Lokálny asistent · údaje #${result.run_id}`;
    const details = document.createElement('details'), summary = document.createElement('summary');
    summary.textContent = 'Údaje použité pri odpovedi a ich pôvod';
    const list = document.createElement('dl'); list.className = 'assistant-facts';
    result.facts.forEach(fact => {
      const term = document.createElement('dt'), value = document.createElement('dd');
      term.textContent = fact.label; value.textContent = `${fact.value} · ${fact.source}`; list.append(term,value);
    });
    details.append(summary,list); article.append(details);
    if (result.proposal) chatProposal(article,result.proposal);
    if (!result.numeric_guard_passed) { const note = document.createElement('p'); note.className = 'footnote'; note.textContent = 'Neoverené číselné hodnoty boli označené priamo v odpovedi. Zvyšok odpovede zostal zobrazený.'; article.append(note); }
    if (result.run_id === state.demo.run_id) chatHistory.push({role:'user',content:question},{role:'assistant',content:result.answer.slice(0,1800)});
    chatHistory = chatHistory.slice(-6);
    if (result.truncated) setText('chat-error','Odpoveď dosiahla limit dĺžky. Položte kratšiu doplňujúcu otázku.');
    $('#chat-messages').scrollTop = $('#chat-messages').scrollHeight;
  } catch (error) {
    pending.remove(); setText('chat-error', error.name === 'AbortError' ? 'Model neodpovedal v časovom limite.' : error.message);
  } finally { clearTimeout(timeout); chatBusy = false; applyAssistantStatus(assistantStatus || {available:false,message:'Skontrolujte Ollamu.'}); }
}
$('#chat-form').addEventListener('submit', event => { event.preventDefault(); const question = $('#chat-question').value.trim(); if (question) { $('#chat-question').value = ''; askAssistant(question); } });
$$('[data-question]').forEach(button => button.addEventListener('click', () => askAssistant(button.dataset.question)));
$('#chat-question').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); $('#chat-form').requestSubmit(); } });
$('#history-run').addEventListener('change', event => { selectedRun = event.target.value; revision++; updateExportLink(); refresh(true); });

function renderTheme() {
  const light = document.documentElement.dataset.theme === 'light';
  setText('theme-icon', light ? '☾' : '☀');
  setText('theme-label', light ? 'Tmavý režim' : 'Svetlý režim');
  $('#theme-toggle').setAttribute('aria-label', light ? 'Prepnúť na tmavý režim' : 'Prepnúť na svetlý režim');
  $('#theme-toggle').setAttribute('aria-pressed', String(light));
  $('meta[name="theme-color"]').content = light ? '#f3f5f9' : '#0b1019';
}
renderTheme();
$('#theme-toggle').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('energia-theme', next); } catch {}
  renderTheme();
  if (state) refresh(true);
});

$$('[data-view]').forEach(el => el.addEventListener('click', () => switchView(el.dataset.view)));
$('.sidebar>.brand').addEventListener('click', event => { event.preventDefault(); switchView('overview'); });
$('#settings-open').addEventListener('click', openSetup);
$('#scenario').addEventListener('change', event => command({scenario:event.target.value}));
$('#speed').addEventListener('change', event => command({speed:Number(event.target.value)}));
$('#play').addEventListener('click', () => state && command({paused:!state.demo.paused}));
$('#step').addEventListener('click', () => command({step:true}));
$$('[data-period]').forEach(el => el.addEventListener('click', () => { period = el.dataset.period; $$('[data-period]').forEach(button => button.classList.toggle('active', button === el)); refresh(true); }));
switchView(location.hash.slice(1));
window.addEventListener('hashchange', () => switchView(location.hash.slice(1)));
async function poll() { await refresh(); refreshIntegrations(); setTimeout(poll, 500); }
applyAssistantStatus({available:false,message:'Kontrolujem lokálny model…'});
setTimeout(poll, 500);
