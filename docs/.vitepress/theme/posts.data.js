import { createContentLoader } from 'vitepress'

function toDateStr(d) {
  if (!d) return ''
  if (typeof d === 'string') return d.slice(0, 10)
  try {
    return new Date(d).toISOString().slice(0, 10)
  } catch {
    return ''
  }
}

function fmt(d) {
  const s = toDateStr(d)
  if (!s) return ''
  const [y, m, day] = s.split('-')
  return `${y}.${m}.${day}`
}

// 扫描 docs/posts/*.md，生成文章列表数据（首页「最新」与 /posts/ 列表共用）
export default createContentLoader('posts/*.md', {
  transform(raw) {
    return raw
      // 必须有 title，且排除 /posts/ 索引页本身
      .filter((p) => p.frontmatter.title && !/\/posts\/?$/.test(p.url))
      .map((p) => ({
        url: p.url,
        title: p.frontmatter.title,
        date: toDateStr(p.frontmatter.date),
        dateText: fmt(p.frontmatter.date),
        tags: p.frontmatter.tags || [],
        excerpt: p.frontmatter.excerpt || '',
      }))
      .sort((a, b) => (a.date < b.date ? 1 : -1))
  },
})
