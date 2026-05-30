// 自动扫描 docs/books 下的每一本书，把章节笔记生成侧边栏
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BOOKS_DIR = path.resolve(__dirname, '../books')

function readMdFiles(dir) {
  if (!fs.existsSync(dir)) return []
  return fs
    .readdirSync(dir)
    .filter(f => f.endsWith('.md') && f.toLowerCase() !== 'readme.md')
    .sort()
}

function titleFromFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8')
  // 优先用第一个 # 标题
  const m = content.match(/^#\s+(.+)$/m)
  if (m) return m[1].trim().slice(0, 60)
  return path.basename(filePath, '.md')
}

function prettifyName(name) {
  // 去掉编号前缀，如 "01_第一部分_..." → "第一部分_..."
  return name.replace(/^[0-9]+[_-]?/, '').replace(/\.md$/, '').replace(/_/g, ' ')
}

export function generateSidebar() {
  if (!fs.existsSync(BOOKS_DIR)) return {}

  const sidebar = {}
  const bookDirs = fs
    .readdirSync(BOOKS_DIR)
    .filter(f => fs.statSync(path.join(BOOKS_DIR, f)).isDirectory())
    .sort()

  for (const book of bookDirs) {
    const bookPath = path.join(BOOKS_DIR, book)
    const files = readMdFiles(bookPath)

    const items = files.map(f => {
      const fullPath = path.join(bookPath, f)
      const slug = f.replace(/\.md$/, '')
      return {
        text: titleFromFile(fullPath) || prettifyName(f),
        link: `/books/${book}/${slug}`
      }
    })

    if (items.length === 0) continue

    sidebar[`/books/${book}/`] = [
      {
        text: book,
        items
      }
    ]
  }

  return sidebar
}
