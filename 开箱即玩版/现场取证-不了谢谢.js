/* ============================================================================
   滚球向前冲「不了谢谢」现场取证
   ----------------------------------------------------------------------------
   用法：
     1) 用「开始游戏（读取进度）.bat」打开游戏，进到皮肤选择页（看得见「不了谢谢」）
     2) 按 F12 打开开发者工具，切到 Console 标签
     3) 把本文件**整段**粘贴进去，回车
     4) 然后正常去点那四个字（多点几下也行）
     5) 把控制台输出整段复制发回

   它会输出三件关键事实：
     · Laya 实际把这次点击派发给了哪个节点（判断是不是被别的东西吃掉了）
     · 那四个字节点自己的矩形、是否可见、该点是否命中
     · 页面版本号 + stage 兜底是否就绪（判断你是不是跑的旧页面）
   ========================================================================== */
(function(){
  if (window.__GQXQC_FORENSIC){ console.log('取证脚本已经在运行了。'); return; }
  window.__GQXQC_FORENSIC = 1;

  var VER = window.__GQXQC_VER__ || '(未知 —— 可能是旧页面/缓存)';
  console.log('%c[取证] 页面版本 ' + VER, 'color:#0a0;font-weight:bold');
  if (typeof Laya === 'undefined' || !Laya.stage){ console.log('[取证] Laya 还没起来，稍后再试。'); window.__GQXQC_FORENSIC = 0; return; }

  function findSkip(){
    var out = [];
    try {
      (function w(n, d){
        if (!n || d > 10) return;
        try { var b = n.SkipBtn; if (b && b.localToGlobal && b.parent) out.push(b); } catch(e){}
        try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
      })(Laya.stage, 0);
    } catch(e){}
    return out;
  }

  function rectOf(b){
    var a = b.localToGlobal(new Laya.Point(0, 0));
    var c = b.localToGlobal(new Laya.Point(b.width, b.height));
    return [Math.round(a.x), Math.round(a.y), Math.round(c.x), Math.round(c.y)];
  }

  function nodeInfo(n){
    if (!n) return '(空)';
    var cls = (n.constructor && n.constructor.name) || '?';
    var path = [], c = n, k = 0;
    while (c && k++ < 6){ path.push(c.name || (c.constructor && c.constructor.name) || '?'); c = c.parent; }
    return cls + ' name=' + (n.name || '(无名)') + ' 链=' + path.join(' < ');
  }

  // Laya 到底把事件给了谁
  window.__lastDown = null; window.__lastClick = null;
  try {
    Laya.stage.on(Laya.Event.MOUSE_DOWN, {}, function(e){
      window.__lastDown = nodeInfo(e.target) + ' @stage(' + Math.round(e.stageX) + ',' + Math.round(e.stageY) + ')';
    });
    Laya.stage.on(Laya.Event.CLICK, {}, function(e){ window.__lastClick = nodeInfo(e.target); });
    console.log('[取证] 已挂上 Laya 事件监听。');
  } catch(e){ console.log('[取证] 挂 Laya 监听失败：' + e); }

  window.addEventListener('mouseup', function(e){
    setTimeout(function(){
      var vw = window.innerWidth, vh = window.innerHeight, dw = 720, dh = 1280;
      var w = Math.min(vw, vh * dw / dh), s = w / dw;
      var left = (vw - w) / 2, top = (vh - w / (dw / dh)) / 2;
      var sx = (e.pageX - left) / s, sy = (e.pageY - top) / s;    // 屏幕 -> stage 设计坐标

      console.log('%c---- 一次点击 ----', 'color:#08f;font-weight:bold');
      console.log(' 视口 ' + vw + 'x' + vh + ' @' + (window.devicePixelRatio || 1) +
                  '  画布区 ' + Math.round(w) + 'x' + Math.round(w / (dw / dh)));
      console.log(' 屏幕 (' + e.clientX + ',' + e.clientY + ') -> 推定 stage (' + sx.toFixed(1) + ',' + sy.toFixed(1) + ')');
      console.log(' Laya 收到的按下目标: ' + (window.__lastDown || '(没收到 —— 事件没进 Laya)'));
      console.log(' Laya 认定的点击目标: ' + (window.__lastClick || '(没收到)'));

      var list = findSkip();
      console.log(' 页面上「不了谢谢」节点数: ' + list.length);
      for (var i = 0; i < list.length; i++){
        var b = list[i];
        console.log('  [' + i + '] ' + nodeInfo(b) +
                    ' 可见=' + b.visible + ' 尺寸=' + b.width + 'x' + b.height +
                    ' 矩形(stage)=' + rectOf(b).join(',') +
                    ' 该点命中=' + b.hitTestPoint(sx, sy));
      }
      var fb = window.__GQXQC_FALLBACK;
      if (fb) console.log(' 兜底: 就绪=' + fb.ready + '  已触发 ' + fb.hits + ' 次  ' + (fb.last || ''));
      window.__lastDown = null; window.__lastClick = null;
    }, 80);
  }, true);

  console.log('%c已挂好监听：现在去点那四个字，然后把控制台内容整段复制发回。',
              'color:#0a0;font-weight:bold');
})();
