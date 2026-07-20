import fs from 'node:fs'
import path from 'node:path'

const TEXT_EXTENSIONS = new Set(['.css', '.html', '.js', '.json', '.mjs', '.vue'])
const ASSET_EXTENSIONS = new Set(['.gif', '.ico', '.jpeg', '.jpg', '.png', '.svg', '.webp'])

function walkFiles(root) {
  if (!fs.existsSync(root)) return []
  const files = []
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const target = path.join(root, entry.name)
    if (entry.isDirectory()) files.push(...walkFiles(target))
    else if (entry.isFile()) files.push(target)
  }
  return files
}

function publicRelative(value) {
  const normalized = String(value || '').replaceAll('\\', '/').replace(/^\/+/, '').split(/[?#]/, 1)[0]
  return ASSET_EXTENSIONS.has(path.posix.extname(normalized).toLowerCase()) ? normalized : ''
}

export function collectRuntimePublicAssets(webRoot) {
  const sourceFiles = [
    ...walkFiles(path.join(webRoot, 'src')).filter(file => TEXT_EXTENSIONS.has(path.extname(file))),
    path.join(webRoot, 'index.html'),
  ].filter(fs.existsSync)
  const assets = new Set(['favicon.ico'])

  for (const file of sourceFiles) {
    const source = fs.readFileSync(file, 'utf8')
    for (const match of source.matchAll(/["'`](\/xya\/[A-Za-z0-9_./-]+\.(?:gif|ico|jpe?g|png|svg|webp)(?:[?#][^"'`\r\n]*)?)["'`]/gi)) {
      const relative = publicRelative(match[1])
      if (relative) assets.add(relative)
    }
    for (const match of source.matchAll(/\basset\(\s*["'`]([A-Za-z0-9_./-]+\.(?:gif|ico|jpe?g|png|svg|webp))["'`]\s*\)/gi)) {
      const relative = publicRelative(`xya/${match[1]}`)
      if (relative) assets.add(relative)
    }
  }

  return [...assets].sort()
}

function removeEmptyDirectories(root, current = root) {
  if (!fs.existsSync(current)) return
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    if (entry.isDirectory()) removeEmptyDirectories(root, path.join(current, entry.name))
  }
  if (current !== root && fs.readdirSync(current).length === 0) fs.rmdirSync(current)
}

export function curateBuiltPublicAssets(webRoot, outDir = 'dist') {
  const publicRoot = path.resolve(webRoot, 'public')
  const outputRoot = path.resolve(webRoot, outDir)
  const keep = new Set(collectRuntimePublicAssets(webRoot))
  const publicFiles = walkFiles(publicRoot)
  let removedFiles = 0

  for (const sourcePath of publicFiles) {
    const relative = path.relative(publicRoot, sourcePath).replaceAll('\\', '/')
    if (keep.has(relative)) continue
    const outputPath = path.resolve(outputRoot, ...relative.split('/'))
    const safePrefix = `${outputRoot}${path.sep}`.toLowerCase()
    if (!outputPath.toLowerCase().startsWith(safePrefix)) {
      throw new Error(`refusing to prune public asset outside build output: ${relative}`)
    }
    if (fs.existsSync(outputPath)) {
      fs.rmSync(outputPath, { force: true })
      removedFiles += 1
    }
  }

  for (const relative of keep) {
    const sourcePath = path.resolve(publicRoot, ...relative.split('/'))
    const outputPath = path.resolve(outputRoot, ...relative.split('/'))
    if (!sourcePath.toLowerCase().startsWith(`${publicRoot}${path.sep}`.toLowerCase())) {
      throw new Error(`runtime public asset escapes public root: ${relative}`)
    }
    if (!fs.existsSync(sourcePath) || !fs.statSync(sourcePath).isFile()) {
      throw new Error(`referenced public asset is missing: ${relative}`)
    }
    if (!fs.existsSync(outputPath)) {
      throw new Error(`Vite did not copy referenced public asset: ${relative}`)
    }
  }

  removeEmptyDirectories(outputRoot)
  const keptBytes = [...keep].reduce((total, relative) => {
    const outputPath = path.resolve(outputRoot, ...relative.split('/'))
    return total + fs.statSync(outputPath).size
  }, 0)
  const manifest = {
    schemaVersion: 1,
    keptFiles: keep.size,
    keptBytes,
    removedFiles,
    assets: [...keep],
  }
  fs.writeFileSync(
    path.join(outputRoot, 'public-assets-manifest.json'),
    `${JSON.stringify(manifest, null, 2)}\n`,
    'utf8',
  )
  return manifest
}
