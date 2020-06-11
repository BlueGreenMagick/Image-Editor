(function () {
    var targetEl = null;
    window.addEventListener("contextmenu", function (e) {
        targetEl = e.target;
    })
    window.addonAnno_getSrc = function(){
        if(targetEl.tagName == "IMG"){
            return targetEl.src
        }else{
            return null
        }
    }
    window.addonAnno_changeSrc = function(src){
        var src = atob(src)
        if(targetEl.tagName == "IMG"){
            targetEl.src = src;
        }else{
            console.log("ERROR")
        }
        
    }

})()
