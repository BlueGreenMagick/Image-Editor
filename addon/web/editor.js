(function () {
  let targetEl = null
  const addonAnno = {}

  addonAnno.addListener = function () {
    const fields = document.getElementsByClassName('field')
    for (let i = 0; i < fields.length; i++) {
      let field = fields[i]
      if (field.shadowRoot) {
        field = field.shadowRoot
      }
      field.addEventListener('contextmenu', function (e) {
        targetEl = e.target
      })
    }
  }

  const selectedIsImage = function () {
    return targetEl.tagName === 'IMG'
  }

  const hasSingleImage = function () {
    const field = window.getCurrentField()
    if (!field) { return false }
    return field.shadowRoot.querySelectorAll('img').length === 1
  }

  addonAnno.imageIsSelected = function () {
    return selectedIsImage() || hasSingleImage()
  }

  addonAnno.getSrc = function () {
    if (targetEl.tagName === 'IMG') {
      return targetEl.src
    } else {
      return null
    }
  }

  addonAnno.changeSrc = function (src) {
    if (targetEl.tagName === 'IMG') {
      targetEl.src = window.atob(src)
    } else {
      console.log('ERROR')
    }
  }

  window.addonAnno = addonAnno
})()
