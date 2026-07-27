/**
 * docsify-meta-card.js
 *
 * 把文章顶部 YAML frontmatter 渲染成一张精致的「元信息卡片」。
 * - 在 docsify beforeEach 钩子里抓取并剥离开头的 --- frontmatter 块;
 * - 解析字段,生成徽章 / 时间线 / 标签 / 关联的卡片 HTML 注入正文顶部;
 * - 不改动任何 .md 文件,frontmatter 原样留给 Python 工具链(仪表盘/侧边栏脚本)。
 * - 不喜欢?注释掉 index.html 里引用本文件的那一行即可全局回滚。
 */
(function () {
  'use strict';

  /* ---------- 1. 注入样式(仅注入一次,与 docsify vue 主题色统一) ---------- */
  var style = document.createElement('style');
  style.textContent = [
    '.kp-meta{margin:1.5rem 0 2rem;padding:14px 18px;background:#f8f9fa;',
    'border:1px solid #eaecef;border-left:4px solid #42b983;border-radius:8px;',
    'font-size:.9em;line-height:1.9;}',
    '.kp-meta__head{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin-bottom:6px;}',
    '.kp-meta__row{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;color:#5a6473;}',
    '.kp-meta__label{margin-right:2px;}',
    '.kp-meta__item{color:#5a6473;}',
    '.kp-meta__item--muted{color:#90a4b5;}',
    '.kp-badge{display:inline-block;padding:2px 10px;border-radius:12px;',
    'font-size:.82em;font-weight:600;color:#fff;background:#909399;white-space:nowrap;}',
    '.kp-badge--domain{background:#42b983;}',
    '.kp-badge--imp{background:#909399;}',
    '.kp-badge--high{background:#e6553a;}',
    '.kp-badge--mid{background:#e6a23c;}',
    '.kp-badge--low{background:#90a4b5;}',
    '.kp-level{font-weight:600;padding:2px 10px;border-radius:12px;font-size:.82em;white-space:nowrap;}',
    '.kp-level--gray{color:#909399;background:#f0f0f0;}',
    '.kp-level--blue{color:#2563eb;background:#e0ecff;}',
    '.kp-level--green{color:#1a8a3a;background:#e3f7eb;}',
    '.kp-level--purple{color:#7c3aed;background:#efe7ff;}',
    '.kp-target{color:#8492a6;font-size:.82em;font-weight:500;}',
    '.kp-arrow{color:#c0c4cc;margin:0 4px;font-size:.82em;}',
    '.kp-tag{display:inline-block;padding:1px 9px;border:1px solid #dcdfe6;',
    'border-radius:10px;font-size:.8em;color:#5a6473;background:#fff;}',
    '.kp-tag--ghost{border-style:dashed;color:#8492a6;}'
  ].join('');
  document.head.appendChild(style);

  /* ---------- 2. 极简 frontmatter 解析器(格式由 templates/skill-template.md 固定) ---------- */
  function parseFrontmatter(text) {
    var meta = {};
    text.split(/\r?\n/).forEach(function (line) {
      var idx = line.indexOf(':');
      if (idx === -1) return;
      var key = line.slice(0, idx).trim();
      var val = line.slice(idx + 1).trim();
      if (!key) return;
      if (/^".*"$/.test(val) || /^'.*'$/.test(val)) val = val.slice(1, -1);
      var arr = /^\[(.*)\]$/.exec(val);
      if (arr) {
        var inner = arr[1].trim();
        meta[key] = inner === '' ? [] : inner.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
      } else {
        meta[key] = val;
      }
    });
    return meta;
  }

  /* ---------- 3. HTML 转义,防注入 ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function badge(cls, text) {
    return '<span class="kp-badge ' + cls + '">' + esc(text) + '</span>';
  }

  var LEVEL_CLASS = { '了解': 'gray', '熟悉': 'blue', '掌握': 'green', '精通': 'purple' };
  var IMP_CLASS = { '高': 'high', '中': 'mid', '低': 'low' };

  /* ---------- 4. 拼装卡片 ---------- */
  function buildCard(m) {
    var rows = [];

    // 徽章行:domain + level→target + importance
    var head = '<div class="kp-meta__head">';
    if (m.domain) head += badge('kp-badge--domain', m.domain);
    if (m.level || m.target) {
      head += '<span class="kp-level kp-level--' + (LEVEL_CLASS[m.level] || 'gray') + '">' +
              esc(m.level || '—') + '</span>';
      if (m.target && m.target !== m.level) {
        head += '<span class="kp-arrow">→</span><span class="kp-target">目标 ' + esc(m.target) + '</span>';
      }
    }
    if (m.importance) head += badge('kp-badge--imp kp-badge--' + (IMP_CLASS[m.importance] || 'mid'), '★ ' + m.importance);
    head += '</div>';
    rows.push(head);

    // 时间线行:last_reviewed → next_review + 考核状态
    if (m.last_reviewed || m.next_review || 'last_assessed' in m) {
      var tl = '<div class="kp-meta__row">';
      if (m.last_reviewed && m.next_review) {
        tl += '<span class="kp-meta__item">🗓 复习 ' + esc(m.last_reviewed) + ' → ' + esc(m.next_review) + '</span>';
      } else if (m.next_review) {
        tl += '<span class="kp-meta__item">🗓 下次复习 ' + esc(m.next_review) + '</span>';
      }
      tl += m.last_assessed
        ? '<span class="kp-meta__item kp-meta__item--muted">上次考核 ' + esc(m.last_assessed) + '</span>'
        : '<span class="kp-meta__item kp-meta__item--muted">待考核</span>';
      tl += '</div>';
      rows.push(tl);
    }

    // 标签行
    if (m.tags && m.tags.length) {
      rows.push('<div class="kp-meta__row"><span class="kp-meta__label">🏷</span>' +
        m.tags.map(function (t) { return '<span class="kp-tag">' + esc(t) + '</span>'; }).join('') +
        '</div>');
    }

    // 关联行
    if (m.related && m.related.length) {
      rows.push('<div class="kp-meta__row"><span class="kp-meta__label">🔗 相关</span>' +
        m.related.map(function (t) { return '<span class="kp-tag kp-tag--ghost">' + esc(t) + '</span>'; }).join('') +
        '</div>');
    }

    return '<div class="kp-meta">' + rows.join('') + '</div>';
  }

  /* ---------- 5. 注册 docsify 插件 ---------- */
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat([
    function (hook) {
      hook.beforeEach(function (markdown) {
        var matched = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(markdown);
        if (!matched) return markdown; // 无 frontmatter(DASHBOARD/README 等)→ 原样渲染
        var meta = parseFrontmatter(matched[1]);
        try {
          return buildCard(meta) + '\n\n' + markdown.slice(matched[0].length);
        } catch (e) {
          return markdown; // 解析异常 → 兜底原样
        }
      });
    }
  ]);
})();
