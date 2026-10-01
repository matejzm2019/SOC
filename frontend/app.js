const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const number = (value, digits = 2) => value == null ? '—' : new Intl.NumberFormat('sk-SK', {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(value);
const kw = watts => `${number(watts / 1000)} kW`;
const eur = value => value == null ? 'Vypnuté' : `${number(value)} €`;
const time = timestamp => new Date(timestamp).toLocaleTimeString('sk-SK', {hour:'2-digit', minute:'2-digit', timeZone:'Europe/Bratislava'});
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state, view = 'overview', period = 'day', settingsTab = 'source', busy = false, refreshing = false, revision = 0;
let lastDataAt = 0, lastDataKey = '';
const pages = {
  overview: ['Prehľad', 'Prehľad domácnosti', 'Spotreba, výroba a tok energie na jednom mieste.'],
  history: ['História', 'Energia v čase', 'Priebeh spotreby a výroby.'],
  forecast: ['Predikcie', 'Predikcia na 24 hodín', 'Odhad podľa minulého dňa.'],
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

function setText(id, value) { $(`#${id}`).textContent = value; }
function metricValue(id, value, unit) { $(`#${id}`).innerHTML = `${number(value)}<small>${unit}</small>`; }

function updateModules() {
  $$('[data-module]').forEach(el => { el.hidden = !state.settings[`${el.dataset.module}_enabled`]; });
  // SVG elements do not consistently implement HTMLElement.hidden.
  $$('svg [data-module]').forEach(el => { el.style.display = state.settings[`${el.dataset.module}_enabled`] ? '' : 'none'; });
  if (view === 'economy' && !state.settings.prices_enabled) switchView('overview');
  $('#path-pv').style.display = state.settings.pv_enabled ? '' : 'none';
  $('#path-battery').style.display = state.settings.battery_enabled ? '' : 'none';
}

function setFlow(id, value, reverse) {
  const path = $(`#path-${id}`);
  path.classList.toggle('reverse', reverse);
  path.classList.toggle('idle', Math.abs(value) < 1 || state.demo.paused);
}

function renderState() {
  const s = state.sample, settings = state.settings, demo = state.demo;
  updateModules();
  $$('[data-demo-control]').forEach(el => { el.hidden = !demo.enabled; });
  setText('mode-title', demo.enabled ? 'Demo režim' : 'Živé monitorovanie');
  setText('mode-pill', demo.enabled ? '◉ Demo režim' : '◉ Živé údaje');
  metricValue('load-value', s.load_w / 1000, 'kW');
  metricValue('pv-value', s.pv_w / 1000, 'kW');
  metricValue('soc-value', s.soc_pct, '%');
  metricValue('grid-value', Math.abs(s.grid_w) / 1000, 'kW');
  setText('load-detail', `${number(s.voltage_v, 0)} V · ${number(s.current_a, 1)} A · virtuálne`);
  setText('pv-detail', `${number(settings.pv_kwp, 1)} kWp inštalovaný výkon`);
  if (s.source === 'hybrid') setText('pv-detail', `${number(s.panel_power_w, 3)} W panel · ${number(s.illuminance_lux, 0)} lx · ESP32`);
  const batteryAction = s.battery_w > 1 ? 'Vybíjanie' : s.battery_w < -1 ? 'Nabíjanie' : 'Pohotovosť';
  setText('battery-detail', `${number(s.battery_energy_kwh, 1)} / ${number(settings.battery_kwh, 1)} kWh · ${batteryAction.toLowerCase()} · virtuálne`);
  $('#soc-bar').style.width = `${s.soc_pct || 0}%`;
  const gridAction = !s.grid_available ? 'Výpadok siete' : s.grid_w > 1 ? '↓ Odber zo siete' : s.grid_w < -1 ? '↑ Dodávka do siete' : 'Bez toku energie';
  setText('grid-detail', gridAction);
  setText('flow-load', kw(s.served_w));
  setText('flow-pv', kw(s.pv_w));
  setText('flow-pv-sub', `${number(settings.pv_kwp, 1)} kWp · virtuálna FV`);
  setText('flow-grid', kw(Math.abs(s.grid_w)));
  setText('flow-grid-sub', gridAction);
  setText('flow-battery', `${s.battery_w > 1 ? '−' : s.battery_w < -1 ? '+' : ''}${kw(Math.abs(s.battery_w))}`);
  $('#flow-battery').parentElement.setAttribute('aria-label', `${batteryAction}, ${s.battery_eta_hours == null ? 'odhad nedostupný' : number(s.battery_eta_hours, 1) + ' hodín do limitu'}`);
  setText('flow-wind', kw(s.wind_w));
  setText('mobile-pv', kw(s.pv_w));
  setText('mobile-load', kw(s.served_w));
  setText('mobile-battery', kw(Math.abs(s.battery_w)));
  setText('mobile-grid', kw(Math.abs(s.grid_w)));
  setText('mobile-grid-detail', gridAction);
  setFlow('pv', s.pv_w, false);
  setFlow('grid', s.grid_w, s.grid_w < 0);
  setFlow('battery', s.battery_w, s.battery_w > 0);
  setFlow('wind', s.wind_w, false);
  setText('flow-status', s.grid_available ? '● SIEŤ DOSTUPNÁ' : '○ OSTROVNÝ REŽIM');
  setText('balance-caption', s.unserved_w > 1 ? `Nepokrytá spotreba ${kw(s.unserved_w)}` : 'Celá spotreba pokrytá');
  const eta = s.battery_eta_hours == null ? '' : ` · do limitu ${number(s.battery_eta_hours, 1)} h`;
  setText('unserved', s.curtailed_w > 1 ? `Obmedzená výroba ${kw(s.curtailed_w)}` : `${settings.battery_enabled ? batteryAction + eta : 'Batéria vypnutá'}`);
  setText('temperature', `${number(s.temperature_c, 0)}°C`);
  setText('weather-condition', s.cloud_pct > 65 ? 'Zamračené' : s.radiation_wm2 > 20 ? 'Prevažne slnečno' : 'Nízke slnečné žiarenie');
  setText('wind-weather', `${number(s.wind_ms, 1)} m/s`);
  setText('cloud-weather', `${number(s.cloud_pct, 0)} %`);
  setText('radiation-weather', `${number(s.radiation_wm2, 0)} W/m²`);
  setText('location', `⌖ ${number(settings.latitude)}°, ${number(settings.longitude)}° · virtuálna lokalita`);
  setText('buy-price', eur(s.buy_eur_kwh));
  setText('sell-price', eur(s.sell_eur_kwh));
  setText('tariff-note', `Distribúcia ${eur(s.distribution_eur_kwh)}/kWh · fix ${eur(s.fixed_eur_day)}/deň`);
  $('#scenario').value = demo.scenario;
  $('#speed').value = demo.speed;
  setText('play', demo.paused ? '▶ Spustiť' : 'Ⅱ Pozastaviť');
  const date = new Date(s.timestamp).toLocaleDateString('sk-SK', {day:'numeric', month:'short', timeZone:'Europe/Bratislava'});
  setText('sim-clock', demo.enabled
    ? `${date} ${time(s.timestamp)} · ${demo.paused ? 'pozastavené' : `1 s ≈ ${demo.speed * 5} min`} · demo čas`
    : `${date} ${time(s.timestamp)} · ${demo.paused ? 'pozastavené' : 'vzorka každú 1 s'} · reálny čas`);
  setText('run-info', `${demo.enabled ? 'Demo experiment' : 'Monitorovanie'} #${demo.run_id} · Europe/Bratislava`);
  const hybrid = settings.measurement_source === 'hybrid';
  setText('device-status', hybrid ? (state.device.online ? '● ESP32 ONLINE' : '○ ESP32 OFFLINE') : 'SIMULÁTOR');
  $('#device-status').classList.toggle('device-offline', hybrid && !state.device.online);
  $('#insights').innerHTML = state.summary.items.map(item => `<article class="insight ${escape(item.kind)}"><h3>${escape(item.title)}</h3><p>${escape(item.text)}</p></article>`).join('');
  if (demo.error) { $('#error').textContent = demo.error; $('#error').hidden = false; }
}

function series() {
  const color = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return [{key:'load_w', color:color('--load'), name:'Spotreba'},
    ...(state.settings.pv_enabled ? [{key:'pv_w', color:color('--solar'), name:'Fotovoltaika'}] : []),
    ...(state.settings.wind_enabled ? [{key:'wind_w', color:color('--wind'), name:'Vietor'}] : [])];
}

function chart(id, points, lines = series(), unit = 'kW') {
  const container = $(`#${id}`);
  if (!points.length) { container.textContent = 'Zatiaľ nie sú dostupné dáta.'; return; }
  const width = Math.max(300, container.clientWidth || 800);
  const height = container.classList.contains('tall') ? 300 : 200;
  const left = 42, right = 15, top = 16, bottom = 32;
  const scale = unit === '%' ? 1 : 1000;
  const values = points.flatMap(p => lines.map(l => (p[l.key] ?? 0) / scale));
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
    const coords = points.map((p, i) => `${x(i)},${y((p[line.key] ?? 0) / scale)}`);
    if (line.key === 'load_w') content += `<path d="M${x(0)},${y(0)} L${coords.join(' L')} L${x(points.length - 1)},${y(0)} Z" fill="${line.color}" opacity=".035"/>`;
    content += `<polyline class="plot-line" stroke="${line.color}" points="${coords.join(' ')}"/>`;
  });
  const ticks = width < 420 ? 4 : 6;
  for (let i = 0; i < ticks; i++) {
    const index = Math.round((points.length - 1) * i / (ticks - 1));
    content += `<text x="${x(index)}" y="${height - 7}" text-anchor="${i === 0 ? 'start' : i === ticks - 1 ? 'end' : 'middle'}">${time(points[index].timestamp)}</text>`;
  }
  points.forEach((point, i) => {
    const tooltip = `${new Date(point.timestamp).toLocaleString('sk-SK', {timeZone:'Europe/Bratislava'})}\n${lines.map(l => `${l.name}: ${number((point[l.key] ?? 0) / scale)} ${unit}`).join('\n')}`;
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
    chart('history-chart', history.points);
    chart('soc-chart', history.points, [{key:'soc_pct', color:getComputedStyle(document.documentElement).getPropertyValue('--battery').trim(), name:'SOC'}], '%');
    const entries = [['Spotreba',t.load_kwh,'kWh','Požadovaný odber'], ['Import zo siete',t.import_kwh,'kWh','Nakúpená energia'], ['Export do siete',t.export_kwh,'kWh','Dodaná energia'], ['Nepokrytá spotreba',t.unserved_kwh,'kWh','Počas výpadku']];
    if (state.settings.pv_enabled) entries.push(['Výroba FV',t.pv_kwh,'kWh','Virtuálna elektráreň']);
    if (state.settings.wind_enabled) entries.push(['Výroba vetra',t.wind_kwh,'kWh','Virtuálna turbína']);
    cards('history-totals', entries);
    setText('history-coverage', `${history.sample_count} vzoriek · ${number(history.duration_hours, 1)} h · ${history.seeded_count} predgenerovaných`);
  }
  if (view === 'economy') {
    cards('economy-totals', [['Čisté náklady',t.cost_eur,'€','Po odpočítaní výkupu'], ['Prevádzková úspora',t.savings_eur,'€','Voči nákupu zo siete'], ['Príjem z exportu',t.export_revenue_eur,'€','Výkup prebytkov'], ['Referenčné náklady',t.reference_eur,'€','Bez lokálnej výroby']]);
    $('#economy-breakdown').innerHTML = [['Odber zo siete',`${number(t.import_kwh)} kWh`],['Dodávka do siete',`${number(t.export_kwh)} kWh`],['Obslúžená spotreba',`${number(t.served_kwh)} kWh`],['Dĺžka výpočtového obdobia',`${number(history.duration_hours,1)} h`],['Náklady vrátane poplatkov',eur(t.cost_eur)],['Rozdiel voči referencii',eur(t.savings_eur)]].map(([a,b]) => `<div><span>${a}</span><strong>${b}</strong></div>`).join('');
  }
}

function renderForecast(result) {
  setText('forecast-model', result.available ? result.model : result.reason);
  chart('forecast-chart', result.points || []);
  const labels = {load_w:'Spotreba', pv_w:'Fotovoltaika', wind_w:'Vietor'};
  setText('forecast-metrics', result.metrics ? Object.entries(result.metrics).filter(([key]) => key === 'load_w' || state.settings[key === 'pv_w' ? 'pv_enabled' : 'wind_enabled']).map(([key,m]) => `${labels[key]}: MAE ${number(m.mae_w,0)} W · RMSE ${number(m.rmse_w,0)} W`).join(' | ') : 'Hodnotenie zatiaľ nie je dostupné. Potrebných je aspoň 48 simulačných hodín; prvých 24 h je predgenerovaných.');
}

async function refresh(forceData = false) {
  if (refreshing || busy) return;
  refreshing = true;
  const requestedView = view;
  const requestedRevision = revision;
  try {
    const nextState = await api('state');
    if (requestedRevision !== revision) return;
    state = nextState;
    $('#error').hidden = true;
    $('#connection').innerHTML = '<i class="online-dot"></i>Lokálne pripojenie';
    renderState();
    const dataKey = `${view}:${period}:${state.demo.run_id}`;
    const interval = view === 'forecast' ? 10000 : 1500;
    if (forceData || dataKey !== lastDataKey || Date.now() - lastDataAt >= interval) {
      const data = await api(view === 'forecast' ? 'forecast' : `history?period=${view === 'history' ? period : 'day'}`);
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
  try { state = await api('demo', {method:'POST', body:JSON.stringify(payload)}); renderState(); }
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
  $$('[data-setting-module]').forEach(el => {
    el.hidden = !form.elements.namedItem(`${el.dataset.settingModule}_enabled`).checked;
    el.querySelector('input').disabled = el.hidden;
  });
  const prices = form.elements.namedItem('prices_enabled').checked;
  $('#price-settings').hidden = !prices;
  $('#prices-disabled').hidden = prices;
  $$('#price-settings input, #price-settings select').forEach(el => el.disabled = !prices);
  const offpeak = prices && form.elements.namedItem('price_mode').value === 'time_of_use';
  $('#offpeak-field').hidden = !offpeak;
  form.elements.namedItem('offpeak_price').disabled = !offpeak;
  const hybrid = form.elements.namedItem('measurement_source').value === 'hybrid';
  setText('source-explainer', hybrid ? 'ESP32-S3 posiela meranie malého panela cez lokálnu Wi-Fi. Kým nie je pripojené, zobrazí sa stav zariadenia; ostatné toky ostávajú simulované.' : 'Simulátor vytvára bezpečné syntetické údaje bez pripojenia zariadenia. Funguje na počítači aj mobile v rovnakej lokálnej sieti.');
  setText('settings-device-state', hybrid ? (state.device.online ? 'ESP32 pripojené' : 'ESP32 nepripojené') : 'Lokálny simulátor');
  const changed = Object.keys(state.settings).filter(key => formSettings()[key] !== state.settings[key]);
  const count = changed.length;
  setText('settings-change-title', count ? `${count} ${count === 1 ? 'zmena' : count < 5 ? 'zmeny' : 'zmien'} na uloženie` : 'Žiadne neuložené zmeny');
  setText('settings-change-detail', count ? 'Uloženie vytvorí nový experiment. Doterajšia história zostane uložená; nový experiment začne pozastavený.' : 'Upravte hodnotu alebo modul. Vzhľad stránky sa prepína okamžite mimo nastavení.');
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
form.addEventListener('change', updateSettings);
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
    state = await api('settings', {method:'PUT', body:JSON.stringify(settings)});
    $('#setup').close(); renderState();
  } catch (error) { setText('setup-error', error.message); }
  finally { busy = false; updateSettings(); }
  refresh(true);
});

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
async function poll() { await refresh(); setTimeout(poll, 500); }
setTimeout(poll, 500);
