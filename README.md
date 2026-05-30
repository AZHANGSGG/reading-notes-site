# 懂叔的出海笔记

[VitePress](https://vitepress.dev/) 个人站，托管在 GitHub Pages：<https://azhangsgg.github.io/reading-notes-site/>

懂叔在新加坡帮中国企业出海。这里是关于出海、地缘、跨文化与投资的文章，以及读书笔记。

## 本地开发

```bash
npm install
npm run dev      # 本地预览 → http://localhost:5173/reading-notes-site/
npm run build    # 构建静态站到 docs/.vitepress/dist
```

## 内容结构

```
docs/
├── posts/       ← 文章。手写 markdown，frontmatter: title / date / tags / excerpt
├── books/       ← 读书笔记，由 sync.py 从 Obsidian 同步生成（勿手改）
├── public/      ← 静态资源 + robots.txt / llms.txt
├── index.md     ← 首页（hero + 最新文章流）
└── about.md     ← 关于
```

## 同步读书笔记

```bash
python3 sync.py            # 从 Obsidian vault 同步读书笔记到 docs/books/
python3 sync.py --dry-run  # 预演，不实际写入
```

> 文章（`docs/posts/`）目前手动维护，不经过 sync.py。

## 部署

push 到 `main` → GitHub Actions（`.github/workflows/deploy.yml`）自动构建并发布到 GitHub Pages。
