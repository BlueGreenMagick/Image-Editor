(function () {
  let targetEl = { tagName: "" }
  let targetElOrd;
  let targetField;
  let verIsOver50 = false;
  const addonAnno = {}

  function getFromSvelteStore(store) {
    let v;
    const unsubscribe = store.subscribe((i) => { v = i });
    unsubscribe();
    return v
  }

  function currentField() {
    if (typeof getCurrentField === 'function') {
      const fieldEl = window.getCurrentField();
      if (!fieldEl) return null;
      return fieldEl.shadowRoot || fieldEl;
    } else { // 2.1.50+
      const noteEditor = window.require("anki/NoteEditor").instances[0];
      const noteInput = getFromSvelteStore(noteEditor.focusedInput);
      if (noteInput === null) return null;
      return noteInput.element;
    }
  }

  addonAnno.addListener = async function () {
    let fields = [];
    if (typeof getCurrentField === 'function') {
      fieldEls = document.getElementsByClassName('field')
      for (const el of fieldEls) {
        fields.push(el.shadowRoot || el);
      }
    } else { // 2.1.50+
      await window.require("anki/ui").loaded;
      const noteFields = window.require("anki/NoteEditor").instances[0].fields;
      fields = await Promise.all(noteFields.map((field) => { return getFromSvelteStore(field.editingArea.editingInputs)[0].element }));
      verIsOver50 = true;
    }

    for (const field of fields) {
      field.addEventListener('contextmenu', function (e) {
        if (verIsOver50) {
          targetField = field;
          const images = field.getElementsByTagName("img");
          for (let i = 0; i < images.length; i++) {
            if (images[i] = e.target) {
              targetElOrd = i;
            }
          }
        }
        targetEl = e.target
      })
    }
  }

  const selectedIsImage = function () {
    return targetEl.tagName === 'IMG'
  }

  const hasSingleImage = function () {
    const field = currentField();
    if (!field) { return false }
    return field.querySelectorAll('img').length === 1
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
    if (verIsOver50) {
      const target = targetField.getElementsByTagName("img")[targetElOrd];
      target.src = atob(src);
    } else {
      targetEl.src = atob(src)
    }
  }

  window.addonAnno = addonAnno
})()
