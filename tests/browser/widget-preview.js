/* Synthetic full-catalog review host, never loaded by the production dashboard. */
(() => {
  'use strict';
  const KINDS = Object.keys(CS2WidgetCatalog);
  const renderers = [];
  let corpus = {};
  const controls = document.querySelector('.preview-controls');
  const stateLabel = document.createElement('label');
  stateLabel.append(document.createTextNode('Données / Data'));
  const stateSelect = document.createElement('select');
  stateSelect.id = 'preview-state'; stateSelect.className='select';
  stateLabel.append(stateSelect); stateLabel.hidden=true;
  const widthLabel = document.createElement('label');
  widthLabel.append(document.createTextNode('Format'));
  const widthSelect = document.createElement('select'); widthSelect.className='select'; widthSelect.id='preview-width';
  for (const [value,label] of [['auto','Auto'],['tablet','Tablette / Tablet'],['phone','Téléphone / Phone']]) widthSelect.add(new Option(label,value));
  widthLabel.append(widthSelect); controls.append(stateLabel,widthLabel);
  const customLabel=document.createElement('label');customLabel.append(document.createTextNode('Personnalisation / Custom'));
  const customSelect=document.createElement('select');customSelect.className='select';customSelect.id='preview-custom';
  customSelect.add(new Option('Auto','auto'));customSelect.add(new Option('Titre long + couleurs / Long title + colors','custom'));
  customLabel.append(customSelect);controls.append(customLabel);
  customSelect.addEventListener('change',()=>window.widgetPreview.customize(customSelect.value==='custom'
    ? {title:'Configuration personnalisée très longue',color:'#76bbfd',background:'#182333',opacity:85,style:'outline'}
    : {title:''}));
  widthSelect.addEventListener('change',()=>{document.body.dataset.previewWidth=widthSelect.value;});
  stateSelect.addEventListener('change',()=>{const entry=corpus[stateSelect.value];if(entry)render(entry.state,entry.demo);});
  const categoryNav=document.createElement('nav');categoryNav.className='preview-categories';
  categoryNav.setAttribute('aria-label','Catégories / Categories');
  document.querySelector('.preview-intro').append(categoryNav);
  const widgets = [];
  const variants = ['standard', 'compact', 'minimal'];
  let previousCategory = null;
  for (const kind of KINDS) {
    const definition = CS2WidgetCatalog[kind];
    if (definition.cat !== previousCategory) {
      previousCategory = definition.cat;
      const categoryHeading = document.createElement('h2');
      categoryHeading.className = 'preview-category-heading';
      CS2I18N.bind(categoryHeading, definition.cat);
      categoryHeading.id='category-'+kind;
      const link=document.createElement('a');link.href='#'+categoryHeading.id;CS2I18N.bind(link, definition.cat);categoryNav.append(link);
      document.getElementById('preview-catalog').append(categoryHeading);
    }
    const section = document.createElement('section');
    section.className = 'preview-section';
    section.dataset.previewKind = kind;
    const heading = document.createElement('header');
    heading.className = 'preview-section-heading';
    const title = document.createElement('h3');
    CS2I18N.bind(title, 'widgets.' + kind + '.title');
    const category = document.createElement('span');
    category.className = 'tiny';
    CS2I18N.bind(category, definition.cat);
    const code = document.createElement('code');
    code.textContent = kind;
    code.setAttribute('translate', 'no');
    heading.append(title, category, code);
    const row = document.createElement('div');
    row.className = 'preview-row';
    for (const variant of variants) {
      const slot = document.createElement('div');
      slot.className = 'preview-slot';
      const label = document.createElement('div');
      label.className = 'preview-variant-label';
      const [width, height] = CCSWidgetPresentation.minimum(kind, variant);
      label.textContent = variant.toUpperCase() + ' · ' + width + ' × ' + height + ' px min.';
      label.setAttribute('translate', 'no');
      const board = document.createElement('div');
      board.className = 'preview-board';
      const renderer = CS2WidgetRenderer({board, format: CS2DisplayFormat, presentation: CCSWidgetPresentation, headingLevel: 4});
      const widget = {id: 'preview-' + kind + '-' + variant, kind, variant,
        title: '', color: '', background: '', opacity: 100, style: 'solid'};
      board.append(renderer.createCard(widget, definition));
      widgets.push(structuredClone(widget));
      renderers.push({renderer, board, kind, variant});
      slot.append(label, board);
      row.append(slot);
    }
    section.append(heading, row);
    document.getElementById('preview-catalog').append(section);
  }
  let last = null;
  let demo = true;
  let anchor = null;
  function render(state, modeDemo = true) {
    last = structuredClone(state);
    demo = modeDemo;
    anchor = state.bomb_timer?.status === 'active'
      ? {at: performance.now(), left: state.bomb_timer.remaining} : null;
    for (const {renderer} of renderers) renderer.updateValues(last, {modeDemo: demo, anchor});
  }
  document.getElementById('preview-catalog').addEventListener('click', event => {
    const control = event.target.closest('[data-demo]');
    if (!control || !demo || !last) return;
    const value = control.dataset.demo;
    const next = structuredClone(last);
    next.bomb_state = value === 'stop' ? 'defused' : 'planted';
    next.bomb_timer = value === 'stop' ? {status: 'idle', enabled: true, duration: 40}
      : {status: 'active', enabled: true, remaining: Number(value), duration: 40};
    render(next, true);
  });
  window.widgetPreview = Object.freeze({
    render,
    setCorpus(next) {
      corpus=structuredClone(next); stateSelect.replaceChildren(...Object.keys(corpus).map(key=>new Option(key,key)));
      stateLabel.hidden=false; stateSelect.value=Object.keys(corpus)[0];
      stateSelect.dispatchEvent(new Event('change'));
    },
    configuration: () => structuredClone(widgets),
    benchmark() {
      const items=renderers.filter(item=>item.variant==='standard');
      const results=[];
      for(const variant of ['compact','minimal','standard']){
        for(let i=0;i<5;i++){
          for(const {renderer,board} of items) renderer.setVariant(board.firstElementChild,variant==='standard'?'compact':'standard');
          document.getElementById('preview-catalog').getBoundingClientRect();
          const start=performance.now();
          for(const {renderer,board} of items) renderer.setVariant(board.firstElementChild,variant);
          document.getElementById('preview-catalog').getBoundingClientRect();
          results.push({operation:'variant29',variant,ms:performance.now()-start});
        }
      }
      return results;
    },
    metrics: () => renderers.map(({board,kind,variant})=>({kind,variant,nodes:board.querySelectorAll('*').length,
      height:board.firstElementChild.getBoundingClientRect().height,
      values:board.querySelectorAll('[data-v]').length})),
    variants: () => renderers.map(({board}) => board.firstElementChild.dataset.variant),
    setVariant(kind, sourceVariant, variant) {
      const item = renderers.find(item => item.kind === kind && item.variant === sourceVariant);
      item.renderer.setVariant(item.board.firstElementChild, variant);
    },
    update() { if (last) render(last, demo); },
    customize(options = {}) {
      for (const {board} of renderers) {
        const card = board.firstElementChild;
        if (options.title !== undefined) {
          const title = card.querySelector('.widget-heading');
          title.textContent = options.title || CS2WidgetCatalog[card.dataset.kind].title;
          if (options.title) { title.setAttribute('translate','no'); delete title.dataset.i18n; }
          else { title.removeAttribute('translate'); CS2I18N.bind(title, 'widgets.' + card.dataset.kind + '.title'); }
        }
        card.style.setProperty('--widget-accent',options.color || '');
        card.style.setProperty('--widget-bg',options.background || '');
        card.style.setProperty('--widget-opacity',(options.opacity ?? 100)+'%');
        card.dataset.style=options.style || 'solid';
      }
    },
  });
  document.getElementById('locale-select').addEventListener('change', () => setTimeout(widgetPreview.update, 0));
})();
