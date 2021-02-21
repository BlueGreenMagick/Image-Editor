(function () {
  let targetEl = null
  window.addEventListener('contextmenu', function (e) {
    targetEl = e.target
  })
  window.addonAnno_getSrc = function () {
    if (targetEl.tagName === 'IMG') {
      return targetEl.src
    } else {
      return null
    }
  }
  window.addonAnno_changeSrc = function (src) {
    if (targetEl.tagName === 'IMG') {
      targetEl.src = window.atob(src)
    } else {
      console.log('ERROR')
    }
  }
})()
