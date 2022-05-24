(function () {
  let targetEl = { tagName: "" };
  let targetElOrd;
  let targetField;
  const addonAnno = {};

  function verIsOver50() {
    return !(typeof getCurrentField === "function");
  }

  function getFromSvelteStore(store) {
    let v;
    const unsubscribe = store.subscribe((i) => {
      v = i;
    });
    unsubscribe();
    return v;
  }

  function currentField() {
    if (typeof getCurrentField === "function") {
      const fieldEl = window.getCurrentField();
      if (!fieldEl) return null;
      return fieldEl.shadowRoot || fieldEl;
    } else {
      // 2.1.50+
      const noteEditor = window.require("anki/NoteEditor").instances[0];
      const noteInput = getFromSvelteStore(noteEditor.focusedInput);
      if (noteInput === null) return null;
      return noteInput.element;
    }
  }

  async function getFieldElements() {
    let fields = [];
    if (!verIsOver50()) {
      fieldEls = document.getElementsByClassName("field");
      for (const el of fieldEls) {
        fields.push(el.shadowRoot || el);
      }
    } else {
      // 2.1.50+
      await window.require("anki/ui").loaded;
      const noteFields = window.require("anki/NoteEditor").instances[0].fields;
      fields = await Promise.all(
        noteFields.map((field) => {
          return getFromSvelteStore(field.editingArea.editingInputs)[0].element;
        })
      );
    }
    return fields;
  }

  addonAnno.addListener = async function () {
    const fields = await getFieldElements();
    for (const field of fields) {
      field.addEventListener("contextmenu", function (e) {
        if (verIsOver50()) {
          targetField = field;
          const images = field.getElementsByTagName("img");
          for (let i = 0; i < images.length; i++) {
            if (images[i] == e.target) {
              targetElOrd = i;
            }
          }
        }
        targetEl = e.target;
      });
    }
  };

  const selectedIsImage = function () {
    return targetEl.tagName === "IMG";
  };

  const hasSingleImage = function () {
    const field = currentField();
    if (!field) {
      return false;
    }
    return field.querySelectorAll("img").length === 1;
  };

  addonAnno.imageIsSelected = function () {
    return selectedIsImage() || hasSingleImage();
  };

  addonAnno.getSrc = function () {
    if (targetEl.tagName === "IMG") {
      return targetEl.src;
    } else {
      return null;
    }
  };

  const targetImage = function () {
    return verIsOver50()
      ? targetField.getElementsByTagName("img")[targetElOrd]
      : targetEl;
  };

  addonAnno.changeAllSrc = async function (src) {
    const newSrc = atob(src);
    const oldSrc = targetImage().src;
    console.log(oldSrc);
    const fields = await getFieldElements();
    for (const field of fields) {
      const imgs = field.querySelectorAll("img");
      for (const img of imgs) {
        if (img.src == oldSrc) {
          console.log("changing");
          img.src = newSrc;
        }
      }
    }
  };

  addonAnno.changeSrc = function (src) {
    targetImage().src = atob(src);
  };

  window.addonAnno = addonAnno;
})();
