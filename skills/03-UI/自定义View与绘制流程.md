---
title: 自定义 View 与绘制流程
domain: 03-UI
level: 了解
target: 精通
importance: 高
last_assessed:
last_reviewed: 2026-07-24
next_review: 2026-10-26
tags: [自定义View, 绘制, measure]
related: [RecyclerView 四级缓存]
---

# 自定义 View 与绘制流程

## 概述
**自定义 View** 的核心是吃透 Android 的**三大绘制流程 measure → layout → draw**,以及触摸事件的处理。`measure` 用 **MeasureSpec**(三种模式)算出 View 尺寸,`layout` 决定它和子 View 的位置,`draw` 用 **Canvas / Paint** 把内容画到屏幕。自定义一个能用的 View 绕不开四件事:正确处理 `wrap_content`(在 `onMeasure` 里测)、`onDraw` 里**绝不新建对象**(否则频繁 GC 卡顿)、分清 `invalidate`(只重绘)与 `requestLayout`(重测重布局)、合理使用硬件加速。它是高级 UI、动画与复杂交互的地基。

## 考核记录
（尚未考核）

## 核心原理 / 关键点

### 1. 为什么需要自定义 View

系统控件覆盖不了所有需求:特殊图形 / 复杂交互(拖拽、手势)、极致性能(避免嵌套层级)、统一封装的复合控件。分两类:**直接继承 View**(完全自己画)、**继承 ViewGroup**(测量并摆放子 View)。

### 2. measure 测量

父级把约束传给子 View,封装成 **MeasureSpec** = 模式 + 尺寸,三种模式:

- **EXACTLY**:`match_parent` 或具体 dp → 尺寸就是 specSize。
- **AT_MOST**:`wrap_content` → 子 View 不能超过 specSize,需自己算。
- **UNSPECIFIED**:不限制(少见,如 ScrollView 测量子项)。

重写 `onMeasure(int wSpec, int hSpec)`:读模式、按内容算尺寸、`setMeasuredDimension(w, h)`。**最常见坑**:`wrap_content` 不处理时,`AT_MOST` 下尺寸被当成 match_parent → `wrap_content` 失效。

### 3. layout 布局

`onLayout(changed, l, t, r, b)`:ViewGroup 在此**定位每个子 View**(调 `child.layout(...)`)。普通 View 一般不用重写。注意:`getWidth()/getHeight()` 是 layout 后的最终尺寸,`getMeasuredWidth()` 是 measure 阶段的测量值。

### 4. draw 绘制

`draw()` 的固定步骤:画背景 → 保存画布层(如有)→ `onDraw`(画自己)→ `dispatchDraw`(画子 View)→ 画装饰(滚动条等)→ 画前景。`onDraw(Canvas)` 里用 **Canvas** 画图形 / 文字、**Paint** 设颜色 / 样式 / 抗锯齿。**铁律:`onDraw` 里绝不 `new` 对象**——draw 每帧都可能执行,频繁分配触发 GC → 卡顿;把 Paint 等做成成员复用。

### 5. invalidate vs requestLayout vs postInvalidate

- **invalidate()**:仅标记重绘(触发 `onDraw`),不重新测量 / 布局;**在 UI 线程调用**。
- **postInvalidate()**:同上,但**可在子线程调用**(内部 post 到主线程),常用于动画刷新。
- **requestLayout()**:标记重新 measure + layout(+ draw);尺寸 / 位置变了才用。
- 误用:只想改外观却 `requestLayout`(多做了测量)、或尺寸变了只 `invalidate`(尺寸不更新)。

### 6. 事件处理(衔接事件分发)

- `onTouchEvent(MotionEvent)`:消费 DOWN / MOVE / UP,返回 true 表示消费。
- 复杂手势用 `GestureDetector` / `ScaleGestureDetector`,避免手写判断。
- 滑动用 `Scroller` / `OverScroller` 配合 `invalidate` 做平滑滚动;支持嵌套滑动实现 `NestedScrollingChild`(与 CoordinatorLayout / RecyclerView 协作)。
- 与「事件分发」(`dispatchTouchEvent` / `onInterceptTouchEvent`)配合,决定谁拿到事件。

### 7. 硬件加速与渲染

- Android 默认**硬件加速**:绘制操作记录成 **DisplayList / RenderNode**,交 GPU 渲染,比软件渲染快。
- 少数 API 硬件层不支持(需查文档),不支持时表现异常 → 临时关闭该 View 硬件层或换等价实现。
- **离屏缓冲 / 软件层**(`LAYER_TYPE_SOFTWARE`):慎用,会额外分配离屏缓冲、拖慢;仅在必要时(复杂遮罩)用。

### 8. 性能与最佳实践

- 避免过度绘制:透明背景、`canvas.clipRect` 限定绘制区、移除无用背景。
- 对象复用:Paint / Path / Rect 做成员,`onDraw` 内复用。
- 自定义属性 `<declare-styleable>`:`obtainStyledAttributes` 取值后**务必 `recycle()`**,命名加前缀防冲突。
- 复合控件优先用 `<merge>` 减层级;能用 ShapeDrawable / 系统属性解决就别自定义。

## 实践经验 / 踩坑

1. **`wrap_content` 失效** —— `onMeasure` 没处理 `AT_MOST`,尺寸变成 match_parent;按内容算并 `setMeasuredDimension`。
2. **`onDraw` 里 new 对象** —— 每帧分配 → GC → 卡顿;Paint 等做成成员复用。
3. **invalidate / requestLayout 混用** —— 改外观用 invalidate、改尺寸用 requestLayout,别搞反。
4. **自定义属性忘 `recycle()` / 命名冲突** —— `obtainStyledAttributes` 后必须 recycle;styleable 名加前缀。
5. **`onDraw` 里做耗时计算 / 同步解码** —— 主线程卡顿;重活预算 / 异步,只把结果画出来。
6. **硬件加速下某些 API 异常** —— 查支持矩阵,必要时局部关硬件层或换等价 API。
7. **不支持嵌套滑动** —— 自定义可滚动 View 没实现 NestedScrolling,与 CoordinatorLayout 嵌套时滚动冲突。

## 待深入 / 下一步

- [ ] 手写一个完整自定义 ViewGroup(测量 + 布局 + 滑动)
- [ ] 读 Choreographer / RenderNode 硬件渲染管线
- [ ] 实战嵌套滑动 `NestedScrollingChild`

## 参考资料

- 自定义 View 指南:https://developer.android.com/develop/ui/views/custom-views/
- Canvas / 绘制:https://developer.android.com/reference/android/graphics/Canvas
- 硬件加速:https://developer.android.com/topic/performance/hardware-accel