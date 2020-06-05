(function () {
    var targetEl = null;
    window.addEventListener("contextmenu", function (e) {
        targetEl = e.target;
    })
    window.addonAnnoChangeSrc = function(src){
        var src = atob(src)
        if(targetEl.tagName == "IMG"){
            targetEl.src = src;
        }else{
            console.log("ERROR")
        }
        
    }

})()
