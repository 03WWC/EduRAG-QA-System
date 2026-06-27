import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

// Configure marked with highlight.js
marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderer = new marked.Renderer()

renderer.code = function ({ text, lang }) {
  if (lang && hljs.getLanguage(lang)) {
    try {
      const highlighted = hljs.highlight(text, { language: lang }).value
      return `<pre><code class="hljs language-${lang}">${highlighted}</code></pre>`
    } catch {
      // fall through
    }
  }
  // Auto-detect language
  try {
    const result = hljs.highlightAuto(text)
    return `<pre><code class="hljs">${result.value}</code></pre>`
  } catch {
    return `<pre><code>${text}</code></pre>`
  }
}

renderer.table = function ({ header, rows }) {
  const headerHtml = header
    .map((cell) => `<th>${cell.text}</th>`)
    .join('')
  const bodyHtml = rows
    .map((row) => `<tr>${row.map((cell) => `<td>${cell.text}</td>`).join('')}</tr>`)
    .join('')
  return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`
}

marked.use({ renderer })

/**
 * Render markdown string to safe HTML
 * @param {string} text - Raw markdown text
 * @returns {string} HTML string
 */
export function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

/**
 * Strip markdown syntax to get plain text (for session previews)
 * @param {string} text
 * @returns {string}
 */
export function stripMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/!\[.*?\]\(.*?\)/g, '')
    .replace(/\[([^\]]*)\]\(.*?\)/g, '$1')
    .replace(/[*_~`#>|]/g, '')
    .replace(/\n+/g, ' ')
    .trim()
}
