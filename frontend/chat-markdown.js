import {Marked, Renderer} from './vendor/marked.esm.js';
import DOMPurify from './vendor/purify.es.mjs';

const escapeHTML = text => String(text).replace(/[&<>"']/g, c => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
}[c]));
const renderer = new Renderer();
// Model output is text, never executable HTML or an automatic image request.
renderer.html = ({text}) => escapeHTML(text);
renderer.image = ({text}) => escapeHTML(text || '');
const markdown = new Marked({gfm:true, breaks:true, renderer});

export function renderChatMarkdown(text) {
  const content = document.createElement('div');
  content.className = 'chat-markdown';
  content.append(DOMPurify.sanitize(markdown.parse(String(text)), {
    ALLOWED_TAGS: ['p','br','h1','h2','h3','h4','h5','h6','strong','em','del',
      'a','blockquote','pre','code','ul','ol','li','hr','table','thead','tbody','tr','th','td'],
    ALLOWED_ATTR: ['href','title','start','align'],
    RETURN_DOM_FRAGMENT: true
  }));
  for (const link of content.querySelectorAll('a')) {
    const href = link.getAttribute('href');
    try {
      const url = new URL(href || '', window.location.href);
      if (!href || !['http:','https:','mailto:'].includes(url.protocol)) throw Error('Unsupported link');
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    } catch {
      link.replaceWith(...link.childNodes);
    }
  }
  for (const table of content.querySelectorAll('table')) {
    const scroll = document.createElement('div');
    scroll.className = 'chat-table-scroll';
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', 'Tabuľka v odpovedi asistenta');
    table.replaceWith(scroll);
    scroll.append(table);
  }
  return content;
}
